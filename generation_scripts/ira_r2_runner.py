"""
IRA R2 — LLM-as-judge run on the 30-task IRA sample.

Loads bench/ira_sample_ids.json, finds each task in the scored partitions,
calls an LLM judge (via OpenRouter) with a rubric-explicit prompt, and writes
per-dimension 0/1 scores to bench/ira_r2_results.json.

Judge model: anthropic/claude-haiku-4-5-20251001 (different family from DeepSeek).

Usage:
    python bench/generation_scripts/ira_r2_runner.py
"""

from __future__ import annotations
import json, os, time
from pathlib import Path
from datetime import datetime, timezone

try:
    from openai import OpenAI
except ImportError:
    raise SystemExit("pip install openai")

from dotenv import load_dotenv
load_dotenv()

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
JUDGE_MODEL = "meta-llama/llama-3.1-8b-instruct"

DIMS = ["signal_fidelity", "tone_compliance", "segment_gate", "confidence_hedging", "format_compliance"]

BANNED_PHRASES = [
    "scaling aggressively", "rapid growth", "explosive growth", "industry leader",
    "cutting-edge", "revolutionize", "bench capacity",
]

JUDGE_PROMPT = """\
You are an independent evaluator for an outreach email benchmark.

Score the candidate email on five binary rubric dimensions (0 = fail, 1 = pass).
Apply each dimension strictly according to its definition. Return only valid JSON.

## Enrichment brief (ground truth signals)
{brief_json}

## Candidate email
Subject: {subject}
Body:
{body}

## Rubric

### signal_fidelity (weight 0.30)
FAIL (0) if the email claims growth, scaling, expansion, momentum, or funding when the brief
does NOT support it (open_roles_estimate <= 2, engineering_velocity = low/unknown, or
no funding evidence). PASS (1) if all claims are supported by the brief or the email
makes no growth claims.

### tone_compliance (weight 0.20)
FAIL (0) if the body contains ANY of these phrases (case-insensitive):
{banned}
Also FAIL if layoff_event=True AND the email uses upbeat/enthusiastic language.
PASS (1) otherwise.

### segment_gate (weight 0.20)
Check whether the email body contains ANY of these exact terms (case-insensitive):
"llm", "large language model", "machine learning platform", "ai capability",
"ai maturity", "ml pipeline", "generative ai", "ai integration", "deploy ai",
"ai roadmap".
FAIL (0) if ANY of these terms appear AND ai_maturity_score < 2.
PASS (1) if NONE of these terms appear, OR if ai_maturity_score >= 2.

### confidence_hedging (weight 0.15)
IMPORTANT: The hedging check IS TRIGGERED (hedging IS REQUIRED) when icp_confidence="low"
OR when low_peer_count=true. These are the conditions that REQUIRE hedging — not conditions
that make hedging optional. "low" confidence means uncertain data → the email must hedge.
Step 1: check if icp_confidence == "low" (exact string) or low_peer_count == true (boolean).
Step 2: if either condition is met, look for hedging words: "may", "might", "some indication",
"limited data", "based on available signals", "appears to", "suggests".
FAIL (0) if the condition IS triggered AND hedging words ARE absent.
PASS (1) if the condition IS triggered AND hedging words ARE present.
PASS (1) if the condition is NOT triggered (icp_confidence != "low" AND low_peer_count != true).

### format_compliance (weight 0.15)
Step 1: Read the subject field exactly. State its first 15 characters verbatim in your
reason. The subject MUST start with the literal characters "[DRAFT]" — not "Context:",
not "YOU WON", not any other prefix. If it does not start with "[DRAFT]", FAIL immediately.
Step 2: Count words in the body (split by spaces). FAIL if word count > 120.
Step 3: Check if body contains "bench capacity" or commits a specific number of
consultants/engineers (e.g. "we have 8 engineers").
FAIL (0) if any of the three checks fail. PASS (1) only if all three pass.

Return JSON only (no markdown):
{{"signal_fidelity": <0|1>, "signal_fidelity_reason": "<one sentence>",
  "tone_compliance": <0|1>, "tone_compliance_reason": "<one sentence>",
  "segment_gate": <0|1>, "segment_gate_reason": "<one sentence>",
  "confidence_hedging": <0|1>, "confidence_hedging_reason": "<one sentence>",
  "format_compliance": <0|1>, "format_compliance_reason": "<one sentence>"}}
"""


def load_sample() -> list[dict]:
    ids = json.loads(Path("bench/ira_sample_ids.json").read_text(encoding="utf-8"))
    index: dict[str, dict] = {}
    for part in ("train", "dev", "held_out"):
        p = Path(f"bench/tenacious_bench_v0.1/{part}.jsonl")
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                t = json.loads(line)
                index[t["task_id"]] = t
    return [index[i] for i in ids if i in index]


def call_judge(client: OpenAI, task: dict) -> dict:
    brief = task["input"]["enrichment_brief"]
    out = task.get("candidate_output", {})
    subject = out.get("email_subject", "")
    body = out.get("email_body", "")
    banned_str = ", ".join(f'"{p}"' for p in BANNED_PHRASES)

    prompt = JUDGE_PROMPT.format(
        brief_json=json.dumps(brief, indent=2),
        subject=subject,
        body=body,
        banned=banned_str,
    )
    resp = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.0,
    )
    raw = resp.choices[0].message.content or ""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])
    return json.loads(raw)


def compute_weighted_score(scores: dict[str, int]) -> float:
    weights = {"signal_fidelity": 0.30, "tone_compliance": 0.20,
               "segment_gate": 0.20, "confidence_hedging": 0.15,
               "format_compliance": 0.15}
    return round(sum(scores.get(d, 0) * w for d, w in weights.items()), 4)


def main() -> None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY not set")

    client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE)
    tasks = load_sample()
    print(f"Loaded {len(tasks)} IRA sample tasks")

    results: list[dict] = []
    failed = 0

    for i, task in enumerate(tasks, 1):
        tid = task["task_id"]
        try:
            judge = call_judge(client, task)
            dim_scores = {d: judge.get(d, 0) for d in DIMS}
            dim_reasons = {d: judge.get(f"{d}_reason", "") for d in DIMS}
            weighted = compute_weighted_score(dim_scores)
            results.append({
                "task_id": tid,
                "category": task.get("category"),
                "r2_dimension_scores": dim_scores,
                "r2_dimension_reasons": dim_reasons,
                "r2_score": weighted,
                "r2_pass": weighted >= 0.75,
                "judge_model": JUDGE_MODEL,
                "run_timestamp": datetime.now(timezone.utc).isoformat(),
            })
            status = "PASS" if weighted >= 0.75 else "FAIL"
            print(f"[{i:02d}/{len(tasks)}] {tid} — {weighted:.2f} ({status})")
        except Exception as e:
            print(f"[{i:02d}/{len(tasks)}] {tid} — ERROR: {e}")
            failed += 1
        time.sleep(0.3)

    output = Path("bench/ira_r2_results.json")
    output.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone. Written {len(results)} results to {output} ({failed} failures)")


if __name__ == "__main__":
    main()
