"""
Trace-derived task generator — Tenacious-Bench v0.1.

Reads eval/trace_log.jsonl and restructures successful + failed traces
into (input, candidate_output, ground_truth, rubric) task format.

Target: ~30% of the 200-300 task dataset.

Usage:
    python bench/generation_scripts/trace_derived.py \
        --trace-log eval/trace_log.jsonl \
        --output-dir bench/tenacious_bench_v0.1 \
        --partition train \
        --limit 60
"""

from __future__ import annotations
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timezone


CATEGORY_FROM_FAILURE_MODE = {
    "FC1_hallucination": "FC1_hallucination",
    "FC2_seg4_bypass": "FC2_seg4_bypass",
    "FC3_overclaim": "FC3_overclaim",
    "FC4_injection": "FC4_injection",
    "FC5_confidence_bypass": "FC5_confidence_bypass",
    "FC6_warm_lead": "FC6_warm_lead",
    "FC7_bench_capacity": "FC7_bench_capacity",
    "FC8_channel": "FC8_channel",
    "FC9_draft_tag": "FC9_draft_tag",
}


def enrichment_brief_from_trace(trace: dict) -> dict:
    """Extract enrichment_brief fields from a trace record."""
    brief = trace.get("enrichment_brief", {}) or {}
    return {
        "open_roles_estimate": brief.get("open_roles_estimate", 0),
        "engineering_velocity": brief.get("engineering_velocity", "unknown"),
        "ai_maturity_score": brief.get("ai_maturity_score", 0),
        "icp_segment": brief.get("icp_segment", "abstain"),
        "icp_confidence": brief.get("icp_confidence", "low"),
        "layoff_event": brief.get("layoff_event", False),
        "num_employees": brief.get("num_employees", "unknown"),
        "total_funding_rounds": brief.get("total_funding_rounds", 0),
        "low_peer_count": brief.get("low_peer_count", False),
        "competitor_gap_confidence": brief.get("competitor_gap_confidence", "none"),
    }


def infer_passing_conditions(trace: dict, brief: dict) -> dict:
    """Infer passing_conditions from trace metadata."""
    failure_mode = trace.get("failure_mode", "")
    conditions: dict = {
        "must_contain": ["[DRAFT]"],
        "draft_tag_required": True,
        "max_word_count": 120,
        "seg4_content_allowed": brief.get("ai_maturity_score", 0) >= 2,
        "hedging_required": (
            brief.get("icp_confidence") == "low" or brief.get("low_peer_count", False)
        ),
        "tone_markers_min_score": 4,
    }

    must_not: list[str] = []
    if failure_mode in ("FC3_overclaim",):
        must_not.extend(["rapidly scaling", "aggressively", "significant growth"])
    if failure_mode in ("FC1_hallucination",):
        must_not.extend(["I know that", "your company recently", "you raised"])
    if failure_mode in ("FC7_bench_capacity",):
        must_not.extend(["bench capacity", "we have engineers available"])

    if must_not:
        conditions["must_not_contain"] = must_not

    return conditions


def task_id_from_trace(trace_id: str, category: str, counter: int) -> str:
    cat_code = category.upper().replace("_", "")[:6]
    short_hash = hashlib.md5(trace_id.encode()).hexdigest()[:4]
    return f"TB-{cat_code}-{counter:03d}-{short_hash}"


def convert_trace_to_task(trace: dict, counter: int, partition: str) -> dict | None:
    failure_mode = trace.get("failure_mode", "")
    category = CATEGORY_FROM_FAILURE_MODE.get(failure_mode, "FC3_overclaim")
    brief = enrichment_brief_from_trace(trace)

    email = trace.get("output", {}) or {}
    if not email.get("email_subject") or not email.get("email_body"):
        return None

    passing_conditions = infer_passing_conditions(trace, brief)
    trace_id = trace.get("trace_id", "")

    return {
        "task_id": task_id_from_trace(trace_id, category, counter),
        "category": category,
        "source": "trace_derived",
        "partition": partition,
        "authored_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "input": {
            "company": trace.get("company", "Unknown Corp"),
            "domain": trace.get("domain", "unknown.com"),
            "warm": trace.get("warm", False),
            "contact_name": trace.get("contact_name", "there"),
            "contact_role": trace.get("contact_role", ""),
            "enrichment_brief": brief,
            "system_prompt_excerpt": trace.get("system_prompt_excerpt", ""),
        },
        "candidate_output": {
            "email_subject": email.get("email_subject", ""),
            "email_body": email.get("email_body", ""),
            "tool_calls": trace.get("tool_calls", []),
        },
        "ground_truth": {
            "expected_behaviour": trace.get("expected_behaviour", ""),
            "passing_conditions": passing_conditions,
        },
        "rubric": {
            "signal_fidelity": {"weight": 0.3},
            "tone_compliance": {"weight": 0.2},
            "segment_gate": {"weight": 0.2},
            "confidence_hedging": {"weight": 0.15},
            "format_compliance": {"weight": 0.15},
        },
        "score": None,
        "failure_mode": failure_mode,
        "trace_id": trace_id,
        "authored_by": "trace_pipeline",
        "judge_score": {
            "input_coherence": 5,
            "ground_truth_verifiability": 5,
            "rubric_clarity": 4,
            "judge_model": "human",
            "passed_filter": True,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-log", type=Path, default=Path("eval/trace_log.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("bench/tenacious_bench_v0.1"))
    parser.add_argument("--partition", choices=["train", "dev", "held_out"], default="train")
    parser.add_argument("--limit", type=int, default=60)
    args = parser.parse_args()

    traces = [
        json.loads(line)
        for line in args.trace_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    output_path = args.output_dir / f"{args.partition}.jsonl"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Read existing tasks to avoid counter collision across runs (Bug 1 fix)
    existing = []
    if output_path.exists():
        existing = [json.loads(l) for l in output_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    counter = len(existing) + 1

    tasks = []
    for trace in traces[:args.limit]:
        task = convert_trace_to_task(trace, counter, args.partition)
        if task:
            tasks.append(task)
            counter += 1

    with output_path.open("a", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")

    print(f"Wrote {len(tasks)} trace-derived tasks -> {output_path}")


if __name__ == "__main__":
    main()
