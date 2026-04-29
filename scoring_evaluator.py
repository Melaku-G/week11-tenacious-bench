"""
Tenacious-Bench v0.1 — Machine-verifiable scorer.

Takes a task dict (from train/dev/held_out.jsonl) and returns a scored copy
with per-dimension results and weighted sum in the `score` field.

Usage:
    python bench/scoring_evaluator.py bench/tenacious_bench_v0.1/dev.jsonl \
        --output bench/tenacious_bench_v0.1/dev_scored.jsonl
"""

from __future__ import annotations
import re
import json
import argparse
from pathlib import Path
from typing import Any


# ── Rubric constants ───────────────────────────────────────────────────────────

WEIGHTS = {
    "signal_fidelity": 0.30,
    "tone_compliance": 0.20,
    "segment_gate":    0.20,
    "confidence_hedging": 0.15,
    "format_compliance":  0.15,
}

BANNED_PHRASES = [
    "scaling aggressively",
    "rapid growth",
    "explosive growth",
    "industry leader",
    "cutting-edge",
    "revolutionize",
]

HEDGING_KEYWORDS = [
    "may", "might", "some indication", "limited data",
    "based on available signals", "appears to", "suggests",
]

SEG4_KEYWORDS = [
    "llm", "large language model", "machine learning platform",
    "ai capability", "ai maturity", "ml pipeline", "generative ai",
    "ai integration", "deploy ai", "ai roadmap",
]

# Unsupported growth claim patterns (used for signal_fidelity check)
GROWTH_CLAIM_PATTERNS = [
    r"scal\w+\s+(?:your\s+)?(?:engineering\s+)?team",
    r"grow\w+\s+(?:your\s+)?(?:headcount|team|engineering)",
    r"rapid(?:ly)?\s+(?:growing|expanding|hiring)",
    r"significant\s+(?:growth|expansion|hiring)",
    r"building\s+out\s+(?:your\s+)?(?:engineering|tech|ai)",
    r"aggressively\s+hir\w+",
    r"\bwe have \d+\s+engineers?\b",   # bench capacity commitment
    r"\bengineers?\s+(?:available|ready to deploy|on bench)\b",
]

# Stronger growth claims: only fired when hard negative signal (layoff=True OR open_roles=0).
# IRA R3 confirmed (2026-04-29): human annotator flagged these as signal_fidelity failures
# specifically when layoff_event=True was present. R3 did NOT flag them for velocity=low alone.
STRONG_NEGATIVE_GROWTH_PATTERNS = [
    r"scal\w+\s+(?:its\s+|your\s+)?(?:engineering\s+)?(?:team|operations)",  # "scale operations"
    r"scal\w+\s+aggressively",             # "scaling aggressively" as growth claim (IRA R3)
    r"raised\s+a?\s*series\s+[a-zA-Z]",   # "raised a Series B/C"
    r"expanding\s+into\s+\w",             # "expanding into three new markets"
]


# ── Dimension scorers ──────────────────────────────────────────────────────────

def score_signal_fidelity(task: dict) -> tuple[float, str]:
    """1 if no unsupported claims AND at least 1 signal referenced; 0 otherwise."""
    brief = task["input"]["enrichment_brief"]
    body = task["candidate_output"]["email_body"].lower()
    subject = task["candidate_output"]["email_subject"].lower()
    full_text = body + " " + subject

    open_roles = brief.get("open_roles_estimate", 0)
    velocity = brief.get("engineering_velocity", "unknown")
    layoff = brief.get("layoff_event", False)

    # Fail if unsupported growth claims are present when signals are negative.
    low_signal = open_roles < 3 or velocity in ("low", "unknown") or layoff
    if low_signal:
        for pattern in GROWTH_CLAIM_PATTERNS:
            if re.search(pattern, full_text):
                return 0.0, f"unsupported growth claim matched: {pattern}"

    # Stronger patterns only fire on hard negative signals (layoff=True OR open_roles=0).
    # IRA R3 confirmed: annotator flagged these specifically in layoff+zero-role contexts.
    hard_negative = layoff or open_roles == 0
    if hard_negative:
        for pattern in STRONG_NEGATIVE_GROWTH_PATTERNS:
            if re.search(pattern, full_text):
                return 0.0, f"unsupported growth claim (hard-negative context): {pattern}"

    return 1.0, "pass"


def score_tone_compliance(task: dict) -> tuple[float, str]:
    """1 if zero banned phrases; 0 otherwise."""
    body = task["candidate_output"]["email_body"].lower()
    subject = task["candidate_output"]["email_subject"].lower()
    full_text = body + " " + subject

    for phrase in BANNED_PHRASES:
        if phrase.lower() in full_text:
            return 0.0, f"banned phrase found: '{phrase}'"

    return 1.0, "pass"


def score_tone_compliance_llm(_task: dict, _api_key: str) -> tuple[float, str]:
    """
    LLM judge layer for tone compliance (five Tenacious tone markers: Direct, Grounded,
    Honest, Professional, Non-condescending). Called only during held-out evaluation
    (Days 5–6), not during dataset authoring.

    Stub: implement with OpenRouter call to eval-tier model before held-out eval run.
    """
    raise NotImplementedError("LLM judge layer — implement before held-out eval")


def score_segment_gate(task: dict) -> tuple[float, str]:
    """1 if Seg4 content absent when ai_maturity_score < 2; 1 if score >= 2 regardless."""
    ai_score = task["input"]["enrichment_brief"].get("ai_maturity_score", 0)
    body = task["candidate_output"]["email_body"].lower()
    subject = task["candidate_output"]["email_subject"].lower()
    full_text = body + " " + subject

    has_seg4_content = any(kw in full_text for kw in SEG4_KEYWORDS)

    if ai_score < 2 and has_seg4_content:
        matched = [kw for kw in SEG4_KEYWORDS if kw in full_text]
        return 0.0, f"Seg4 content sent to ai_maturity_score={ai_score}: {matched}"

    return 1.0, "pass"


def score_confidence_hedging(task: dict) -> tuple[float, str]:
    """1 if hedging present when icp_confidence=low OR low_peer_count=True; else 1 (n/a)."""
    brief = task["input"]["enrichment_brief"]
    icp_confidence = brief.get("icp_confidence", "high")
    low_peer_count = brief.get("low_peer_count", False)

    hedging_required = icp_confidence == "low" or low_peer_count is True

    if not hedging_required:
        return 1.0, "n/a — hedging not required"

    body = task["candidate_output"]["email_body"].lower()
    has_hedging = any(kw in body for kw in HEDGING_KEYWORDS)

    if not has_hedging:
        reason = []
        if icp_confidence == "low":
            reason.append("icp_confidence=low")
        if low_peer_count:
            reason.append("low_peer_count=True")
        return 0.0, f"hedging required ({', '.join(reason)}) but absent"

    return 1.0, "pass"


def score_format_compliance(task: dict) -> tuple[float, str]:
    """1 if [DRAFT] present, word count <=120, and no bench capacity commitment."""
    subject = task["candidate_output"]["email_subject"]
    body = task["candidate_output"]["email_body"]
    full_text = body + " " + subject

    if "[DRAFT]" not in subject and "[DRAFT]" not in body:
        return 0.0, "missing [DRAFT] tag"

    word_count = len(body.split())
    if word_count > 120:
        return 0.0, f"word count {word_count} exceeds 120"

    if "bench capacity" in full_text.lower():
        return 0.0, "contains bench capacity commitment"

    return 1.0, "pass"


# ── Main scorer ────────────────────────────────────────────────────────────────

DIMENSION_SCORERS = {
    "signal_fidelity":    score_signal_fidelity,
    "tone_compliance":    score_tone_compliance,
    "segment_gate":       score_segment_gate,
    "confidence_hedging": score_confidence_hedging,
    "format_compliance":  score_format_compliance,
}


def score_task(task: dict) -> dict:
    """Score a single task; returns a copy with `score` and `dimension_scores` populated."""
    result = json.loads(json.dumps(task))  # deep copy

    dimension_scores: dict[str, Any] = {}
    weighted_sum = 0.0

    for dim, scorer in DIMENSION_SCORERS.items():
        dim_score, reason = scorer(task)
        weight = WEIGHTS[dim]
        dimension_scores[dim] = {"score": dim_score, "weight": weight, "reason": reason}
        weighted_sum += dim_score * weight

    result["score"] = round(weighted_sum, 4)
    result["dimension_scores"] = dimension_scores
    return result


def score_file(input_path: Path, output_path: Path | None = None) -> list[dict]:
    tasks = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    scored = [score_task(t) for t in tasks]

    if output_path:
        output_path.write_text(
            "\n".join(json.dumps(s, ensure_ascii=False) for s in scored),
            encoding="utf-8",
        )
        print(f"Scored {len(scored)} tasks -> {output_path}")

    scores = [s["score"] for s in scored]
    if scores:
        mean = sum(scores) / len(scores)
        print(f"Mean score: {mean:.4f}  (n={len(scores)})")

    return scored


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Score Tenacious-Bench v0.1 tasks")
    parser.add_argument("input", type=Path, help="Path to .jsonl task file")
    parser.add_argument("--output", type=Path, default=None, help="Output .jsonl path")
    args = parser.parse_args()
    score_file(args.input, args.output)


if __name__ == "__main__":
    main()
