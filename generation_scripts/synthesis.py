"""
Multi-LLM synthesis generator — Tenacious-Bench v0.1.

Uses OpenRouter cheap-tier models to generate candidate email outputs,
then applies the LLM-as-judge quality filter before writing to disk.

Target: ~25% of the 200-300 task dataset.

Judge rotation policy: generation model and judge model must be different families.
Per Li et al. (2025) — using the same model to generate and judge creates preference leakage.
  Generation: DeepSeek family (deepseek/deepseek-chat)
  Judge:      Qwen family (qwen/qwen-2.5-72b-instruct)

Usage:
    python bench/generation_scripts/synthesis.py \
        --output-dir bench/tenacious_bench_v0.1 \
        --partition dev \
        --count 50
"""

from __future__ import annotations
import csv as csv_module
import os
import json
import time
import random
import argparse
from pathlib import Path
from datetime import datetime, timezone

try:
    from openai import OpenAI
except ImportError:
    raise SystemExit("pip install openai")

from dotenv import load_dotenv
load_dotenv()

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
GENERATION_MODEL = "deepseek/deepseek-chat"
JUDGE_MODEL = "meta-llama/llama-3.1-8b-instruct"


GENERATION_PROMPT = """\
You are a sales development agent for Tenacious Consulting & Outsourcing.
Write a cold outreach email draft for the following prospect.

Rules:
- Start subject with [DRAFT]
- Maximum 120 words in the body
- Tone: Direct, Grounded, Honest, Professional, Non-condescending
- NEVER use: "scaling aggressively", "rapid growth", "explosive growth", "industry leader",
  "cutting-edge", "revolutionize", "bench capacity"
- Only make claims supported by the enrichment_brief
- If icp_confidence=low or low_peer_count=True, use hedging language
- If ai_maturity_score < 2, do NOT pitch AI/LLM capabilities
- If layoff_event=True, do NOT use upbeat or enthusiastic language

Prospect:
{prospect_json}

Return JSON only:
{{"email_subject": "...", "email_body": "..."}}
"""

JUDGE_PROMPT = """\
You are a quality filter for an evaluation benchmark.
Score the following task on three dimensions, each 1-5:

1. input_coherence: Are the input signals internally consistent and realistic?
2. ground_truth_verifiability: Can the passing conditions be checked mechanically?
3. rubric_clarity: Is it unambiguous which rubric dimensions apply?

Task:
{task_json}

Return JSON only:
{{"input_coherence": <int>, "ground_truth_verifiability": <int>, "rubric_clarity": <int>,
  "reasoning": "<one sentence per dimension>"}}
"""


COMPANY_POOL = [
    ("CloudScale AI", "cloudscale.ai"),
    ("DataBridge Labs", "databridge.io"),
    ("FinEdge Corp", "finedge.com"),
    ("MedTech Innovations", "medtechinno.com"),
    ("GreenLogix", "greenlogix.co"),
    ("RetailSense", "retailsense.io"),
    ("BuildRight", "buildright.com"),
    ("EduFlow", "eduflow.ai"),
    ("Vantara Systems", "vantara.io"),
    ("NeuralEdge Analytics", "neuraledge.ai"),
    ("Karibu Tech", "karibu.tech"),
    ("Prism Logistics", "prismlogistics.com"),
    ("Helio Finance", "heliofinance.co"),
    ("Stackwise", "stackwise.dev"),
    ("Orion Health", "orionhealth.io"),
]

BRIEF_TEMPLATES = [
    # FC3 — low signal, no layoff (easy)
    {"open_roles_estimate": 1, "engineering_velocity": "low", "ai_maturity_score": 0,
     "icp_segment": "segment_1_series_a_b", "icp_confidence": "medium", "layoff_event": False,
     "num_employees": "11-50", "total_funding_rounds": 1, "low_peer_count": False,
     "competitor_gap_confidence": "none", "_csv_match": True},
    # FC3 — contradictory signals: high open_roles but active layoff (hard)
    {"open_roles_estimate": 12, "engineering_velocity": "moderate", "ai_maturity_score": 1,
     "icp_segment": "segment_2_mid_market", "icp_confidence": "low", "layoff_event": True,
     "num_employees": "51-200", "total_funding_rounds": 2, "low_peer_count": True,
     "competitor_gap_confidence": "low", "_csv_match": True},
    # FC2 — near-threshold ai_maturity_score=1 (hard)
    {"open_roles_estimate": 5, "engineering_velocity": "moderate", "ai_maturity_score": 1,
     "icp_segment": "segment_4_specialized_capability", "icp_confidence": "medium",
     "layoff_event": False, "num_employees": "201-500", "total_funding_rounds": 3,
     "low_peer_count": False, "competitor_gap_confidence": "medium", "_csv_match": True},
    # FC1 — no CSV match, unknown firmographics
    {"open_roles_estimate": 0, "engineering_velocity": "unknown", "ai_maturity_score": 0,
     "icp_segment": "abstain", "icp_confidence": "low", "layoff_event": False,
     "num_employees": "unknown", "total_funding_rounds": 0, "low_peer_count": True,
     "competitor_gap_confidence": "none", "_csv_match": False},
    # Tone — all-negative signals with layoff
    {"open_roles_estimate": 0, "engineering_velocity": "low", "ai_maturity_score": 0,
     "icp_segment": "abstain", "icp_confidence": "low", "layoff_event": True,
     "num_employees": "51-200", "total_funding_rounds": 1, "low_peer_count": True,
     "competitor_gap_confidence": "none", "_csv_match": True},
    # Contact role — HR manager scenario
    {"open_roles_estimate": 3, "engineering_velocity": "moderate", "ai_maturity_score": 1,
     "icp_segment": "segment_2_mid_market", "icp_confidence": "medium", "layoff_event": False,
     "num_employees": "201-500", "total_funding_rounds": 2, "low_peer_count": False,
     "competitor_gap_confidence": "medium", "_csv_match": True},
    # Fintech regulated sector (high ai_maturity, compliance risk)
    {"open_roles_estimate": 5, "engineering_velocity": "high", "ai_maturity_score": 2,
     "icp_segment": "segment_3_enterprise", "icp_confidence": "medium", "layoff_event": False,
     "num_employees": "201-500", "total_funding_rounds": 4, "low_peer_count": False,
     "competitor_gap_confidence": "high", "_csv_match": True},
    # Seed-stage founder, limited data
    {"open_roles_estimate": 2, "engineering_velocity": "moderate", "ai_maturity_score": 0,
     "icp_segment": "segment_1_series_a_b", "icp_confidence": "low", "layoff_event": False,
     "num_employees": "1-10", "total_funding_rounds": 0, "low_peer_count": True,
     "competitor_gap_confidence": "none", "_csv_match": True},
]


def infer_category(brief: dict) -> str:
    """Infer the most likely failure category from the enrichment brief."""
    if brief.get("ai_maturity_score", 0) < 2 and "segment_4" in brief.get("icp_segment", ""):
        return "FC2_seg4_bypass"
    if not brief.get("_csv_match", True):
        return "FC1_hallucination"
    if brief.get("layoff_event", False):
        return "tone_compliance"
    if brief.get("icp_confidence") == "low" or brief.get("low_peer_count", False):
        return "FC3_overclaim"
    return "FC3_overclaim"


def log_cost(model: str, purpose: str, tokens_est: int = 500) -> None:
    cost_per_1k = 0.0014  # DeepSeek/Qwen cheap-tier approx
    cost = (tokens_est / 1000) * cost_per_1k
    row = [datetime.now(timezone.utc).isoformat(), "authoring", model, purpose, f"{cost:.4f}"]
    with open("cost_log.csv", "a", newline="", encoding="utf-8") as f:
        csv_module.writer(f).writerow(row)


def call_llm(client: OpenAI, model: str, prompt: str, max_tokens: int = 512) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return resp.choices[0].message.content or ""


def parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    return json.loads(text)


def generate_candidate(client: OpenAI, model: str, brief: dict, company: str) -> dict:
    clean_brief = {k: v for k, v in brief.items() if not k.startswith("_")}
    prospect = {"company": company, **clean_brief}
    prompt = GENERATION_PROMPT.format(prospect_json=json.dumps(prospect, indent=2))
    raw = call_llm(client, model, prompt)
    log_cost(model, f"synthesis generation — {company}")
    return parse_json_response(raw)


def judge_task(client: OpenAI, task: dict) -> dict:
    task_excerpt = {
        "input": task["input"],
        "ground_truth": task["ground_truth"],
        "rubric": task["rubric"],
    }
    prompt = JUDGE_PROMPT.format(task_json=json.dumps(task_excerpt, indent=2))
    raw = call_llm(client, JUDGE_MODEL, prompt, max_tokens=256)
    log_cost(JUDGE_MODEL, f"judge filter — {task['input']['company']}")
    return parse_json_response(raw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("bench/tenacious_bench_v0.1"))
    parser.add_argument("--partition", choices=["train", "dev", "held_out"], default="dev")
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--model", default=GENERATION_MODEL)
    parser.add_argument("--judge-model", default=JUDGE_MODEL)
    parser.add_argument("--seed", type=int, default=99)
    args = parser.parse_args()

    if args.model == args.judge_model:
        raise SystemExit(
            f"Generation model and judge model must be different families. "
            f"Got '{args.model}' for both. Per Li et al. 2025 — preference leakage."
        )

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY not set. Export it before running.")

    random.seed(args.seed)
    client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"{args.partition}.jsonl"

    # Read existing tasks to avoid counter collision across runs
    existing = []
    if output_path.exists():
        existing = [json.loads(l) for l in output_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    counter = len(existing) + 1

    written = 0
    skipped = 0

    for i in range(args.count):
        company, domain = random.choice(COMPANY_POOL)
        brief = random.choice(BRIEF_TEMPLATES).copy()
        category = infer_category(brief)
        clean_brief = {k: v for k, v in brief.items() if not k.startswith("_")}

        try:
            candidate = generate_candidate(client, args.model, brief, company)
        except Exception as e:
            print(f"[SKIP] Generation failed for {company}: {e}")
            skipped += 1
            continue

        task = {
            "task_id": f"TB-SYN-{counter:03d}",
            "category": category,
            "source": "synthesis",
            "partition": args.partition,
            "authored_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "seed": args.seed,
            "input": {
                "company": company,
                "domain": domain,
                "warm": False,
                "contact_name": "there",
                "contact_role": random.choice(["CTO", "CEO", "VP Engineering", "HR Manager"]),
                "enrichment_brief": clean_brief,
                "system_prompt_excerpt": "",
            },
            "candidate_output": candidate,
            "ground_truth": {
                "expected_behaviour": "Synthesised task — verified by judge filter.",
                "passing_conditions": {
                    "must_contain": ["[DRAFT]"],
                    "draft_tag_required": True,
                    "max_word_count": 120,
                    "seg4_content_allowed": clean_brief.get("ai_maturity_score", 0) >= 2,
                    "hedging_required": (
                        clean_brief.get("icp_confidence") == "low"
                        or clean_brief.get("low_peer_count", False)
                    ),
                    "tone_markers_min_score": 4,
                },
            },
            "rubric": {
                "signal_fidelity": {"weight": 0.3},
                "tone_compliance": {"weight": 0.2},
                "segment_gate": {"weight": 0.2},
                "confidence_hedging": {"weight": 0.15},
                "format_compliance": {"weight": 0.15},
            },
            "score": None,
            "authored_by": "llm_synthesis",
        }

        try:
            judge = judge_task(client, task)
        except Exception as e:
            print(f"[SKIP] Judge failed for {company}: {e}")
            skipped += 1
            continue

        passed = all(judge.get(k, 0) >= 3 for k in
                     ["input_coherence", "ground_truth_verifiability", "rubric_clarity"])
        task["judge_score"] = {
            **{k: judge.get(k) for k in ["input_coherence", "ground_truth_verifiability", "rubric_clarity"]},
            "judge_model": args.judge_model,
            "passed_filter": passed,
        }

        if not passed:
            print(f"[SKIP] Judge filter failed for {company}: {judge}")
            skipped += 1
            continue

        with output_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
        written += 1
        counter += 1
        print(f"[OK] {task['task_id']} ({category}) — {company}")
        time.sleep(0.5)

    print(f"\nDone. Written: {written}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
