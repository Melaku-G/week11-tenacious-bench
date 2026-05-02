"""
Day 6 ablation script — run SFT model on held_out.jsonl, score outputs, compute ΔB.

Usage (Colab T4 after training):
    !python bench/training/inference_ablation.py \
        --adapter-dir bench/adapter/tenacious-lora-v2 \
        --held-out bench/tenacious_bench_v0.1/held_out.jsonl \
        --output bench/training/ablation_results.json

Writes:
    bench/training/ablation_results.json   — per-task scores + ΔB summary
"""

from __future__ import annotations
import json
import re
import argparse
from pathlib import Path

try:
    from unsloth import FastLanguageModel
    UNSLOTH = True
except ImportError:
    UNSLOTH = False
    print("[WARN] unsloth not installed — run on Colab T4.")

try:
    import torch
    TORCH = True
except ImportError:
    TORCH = False

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench.scoring_evaluator import score_task


SYSTEM_PROMPT = """\
You are a B2B sales development agent for Tenacious Consulting & Outsourcing.
Write a concise outreach email draft grounded in the enrichment signals provided.

Rules:
- Subject must start with [DRAFT]
- Body must be <=120 words
- Tone: Direct, Grounded, Honest, Professional, Non-condescending
- Only claim what the enrichment_brief supports
- If icp_confidence=low or low_peer_count=True, use hedging language
- If ai_maturity_score < 2, do NOT pitch AI/LLM capabilities
- If layoff_event=True, do NOT use upbeat or enthusiastic language
- NEVER use any of these banned phrases (Style Guide v2 full list):
  scaling aggressively, rapid growth, explosive growth, industry leader,
  cutting-edge, revolutionize, world-class, world class, top talent, a-players,
  rockstar, ninja, wizard, skyrocket, supercharge,
  i hope this email finds you well, just following up, circling back,
  quick question, quick chat, synergize, synergy, leverage, ecosystem,
  game-changer, game changer, disruptor, paradigm shift,
  you'll regret, don't miss out, do not miss out, per my last
- NEVER use the word "bench" when writing to a prospect
- NEVER make bench capacity commitments ("we have X engineers ready")"""

MAX_NEW_TOKENS = 300


def format_input(task: dict) -> str:
    inp = task["input"]
    brief = inp["enrichment_brief"]
    return (
        f"Company: {inp['company']}\n"
        f"Domain: {inp['domain']}\n"
        f"Contact: {inp.get('contact_name', 'there')} ({inp.get('contact_role', '')})\n"
        f"Warm lead: {inp['warm']}\n"
        f"Enrichment brief:\n{json.dumps(brief, indent=2)}\n"
    )


def parse_output(text: str) -> tuple[str, str]:
    """Extract (email_subject, email_body) from model output."""
    # Strip any trailing <|im_end|> tokens
    text = re.sub(r"<\|im_end\|>.*", "", text, flags=re.DOTALL).strip()

    subject_match = re.search(r"(?i)subject:\s*(.+)", text)
    subject = subject_match.group(1).strip() if subject_match else "[DRAFT] (parse error)"

    # Body: everything after the subject line + blank line
    body_match = re.split(r"(?i)subject:\s*.+\n+", text, maxsplit=1)
    body = body_match[1].strip() if len(body_match) > 1 else text.strip()

    return subject, body


def run_inference(adapter_dir: Path, tasks: list[dict]) -> list[dict]:
    if not UNSLOTH or not TORCH:
        raise RuntimeError("unsloth/torch not available — run on Colab T4.")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(adapter_dir),
        max_seq_length=1024,
        load_in_4bit=True,
        dtype=None,
    )
    FastLanguageModel.for_inference(model)

    results = []
    for i, task in enumerate(tasks):
        user_msg = format_input(task)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(model.device)

        with torch.no_grad():
            output_ids = model.generate(
                input_ids,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=0.0,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        generated = tokenizer.decode(
            output_ids[0][input_ids.shape[1]:],
            skip_special_tokens=True,
        )
        subject, body = parse_output(generated)

        # Build a scored task using the model's output
        task_copy = json.loads(json.dumps(task))
        task_copy["candidate_output"] = {
            "email_subject": subject,
            "email_body": body,
        }
        scored = score_task(task_copy)
        scored["sft_raw_output"] = generated
        results.append(scored)

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(tasks)}] score={scored['score']:.2f}")

    return results


def compute_delta(baseline_tasks: list[dict], sft_results: list[dict]) -> dict:
    baseline_scores = [t.get("score", 0) for t in baseline_tasks]
    sft_scores = [t.get("score", 0) for t in sft_results]

    b_mean = sum(baseline_scores) / len(baseline_scores)
    sft_mean = sum(sft_scores) / len(sft_scores)

    b_pass = sum(1 for s in baseline_scores if s >= 0.75) / len(baseline_scores)
    sft_pass = sum(1 for s in sft_scores if s >= 0.75) / len(sft_scores)

    # Per-dimension pass rates
    dims = ["signal_fidelity", "tone_compliance", "segment_gate", "confidence_hedging", "format_compliance"]
    dim_delta = {}
    for d in dims:
        b_dim = [t.get("dimension_scores", {}).get(d, {}).get("score", 0) for t in baseline_tasks]
        s_dim = [t.get("dimension_scores", {}).get(d, {}).get("score", 0) for t in sft_results]
        dim_delta[d] = {
            "baseline_pass": round(sum(1 for x in b_dim if x >= 1.0) / len(b_dim), 4),
            "sft_pass": round(sum(1 for x in s_dim if x >= 1.0) / len(s_dim), 4),
            "delta": round(
                sum(1 for x in s_dim if x >= 1.0) / len(s_dim) -
                sum(1 for x in b_dim if x >= 1.0) / len(b_dim), 4
            ),
        }

    return {
        "n_tasks": len(baseline_tasks),
        "baseline_mean_score": round(b_mean, 4),
        "sft_mean_score": round(sft_mean, 4),
        "delta_mean": round(sft_mean - b_mean, 4),
        "baseline_pass_rate": round(b_pass, 4),
        "sft_pass_rate": round(sft_pass, 4),
        "delta_pass_rate": round(sft_pass - b_pass, 4),
        "per_dimension": dim_delta,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter-dir", type=Path,
                        default=Path("bench/adapter/tenacious-lora-v2"))
    parser.add_argument("--held-out", type=Path,
                        default=Path("bench/tenacious_bench_v0.1/held_out.jsonl"))
    parser.add_argument("--output", type=Path,
                        default=Path("bench/training/ablation_results.json"))
    args = parser.parse_args()

    baseline_tasks = [
        json.loads(l) for l in args.held_out.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    print(f"Loaded {len(baseline_tasks)} held-out tasks")
    print(f"Baseline pass rate: {sum(1 for t in baseline_tasks if t.get('score',0)>=0.75)/len(baseline_tasks):.1%}")

    print("\nRunning SFT inference...")
    sft_results = run_inference(args.adapter_dir, baseline_tasks)

    summary = compute_delta(baseline_tasks, sft_results)

    output = {
        "summary": summary,
        "per_task": [
            {
                "task_id": r.get("task_id"),
                "baseline_score": b.get("score"),
                "sft_score": r.get("score"),
                "delta": round(r.get("score", 0) - b.get("score", 0), 4),
                "sft_dimension_scores": r.get("dimension_scores"),
            }
            for b, r in zip(baseline_tasks, sft_results)
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n── Ablation Results ──────────────────────────────")
    print(f"  n tasks:            {summary['n_tasks']}")
    print(f"  Baseline pass rate: {summary['baseline_pass_rate']:.1%}")
    print(f"  SFT pass rate:      {summary['sft_pass_rate']:.1%}")
    print(f"  ΔB (pass rate):     {summary['delta_pass_rate']:+.1%}")
    print(f"  Baseline mean:      {summary['baseline_mean_score']:.4f}")
    print(f"  SFT mean:           {summary['sft_mean_score']:.4f}")
    print(f"  ΔB (mean score):    {summary['delta_mean']:+.4f}")
    print(f"\nPer-dimension delta:")
    for d, v in summary["per_dimension"].items():
        print(f"  {d:<25} baseline={v['baseline_pass']:.1%}  sft={v['sft_pass']:.1%}  Δ={v['delta']:+.1%}")
    print(f"\nResults -> {args.output}")


if __name__ == "__main__":
    main()
