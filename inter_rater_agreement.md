# Inter-Rater Agreement — Tenacious-Bench v0.1

## Purpose

Validates that the five machine-verifiable rubric dimensions produce consistent scores
across independent raters (automated scorer vs human annotator vs LLM judge).

---

## Protocol

### Sample
50 tasks randomly drawn from the dev partition, stratified by category (10 per failure class).

### Raters
| Rater | Type | Tool |
|-------|------|------|
| R1 | Automated | `bench/scoring_evaluator.py` |
| R2 | LLM judge | Claude Sonnet 4.6, 0-shot rubric prompt |
| R3 | Human | Tenacious team annotator |

### Procedure
1. R1 runs `scoring_evaluator.py` on the 50-task sample → scores recorded.
2. R2 receives each task as a structured prompt with the rubric; returns per-dimension 0/1 + reason.
3. R3 scores each task independently, recording per-dimension decision + 1-sentence justification.
4. Agreement computed per dimension and overall.

---

## Metrics

**Cohen's κ** (pairwise, per dimension):

| Dimension | R1 vs R2 | R1 vs R3 | R2 vs R3 | Target κ |
|-----------|----------|----------|----------|---------|
| signal_fidelity | TODO | TODO | TODO | ≥ 0.70 |
| tone_compliance | TODO | TODO | TODO | ≥ 0.80 |
| segment_gate | TODO | TODO | TODO | ≥ 0.85 |
| confidence_hedging | TODO | TODO | TODO | ≥ 0.70 |
| format_compliance | TODO | TODO | TODO | ≥ 0.90 |
| **Overall** | TODO | TODO | TODO | ≥ 0.75 |

**Percent agreement** (pairwise):

| Dimension | R1 vs R2 | R1 vs R3 | R2 vs R3 |
|-----------|----------|----------|----------|
| signal_fidelity | TODO | TODO | TODO |
| tone_compliance | TODO | TODO | TODO |
| segment_gate | TODO | TODO | TODO |
| confidence_hedging | TODO | TODO | TODO |
| format_compliance | TODO | TODO | TODO |

---

## Disagreement Analysis

Cases where any two raters disagree are reviewed jointly. Resolution:
- If R3 (human) disagrees with both R1 and R2 → review rubric definition; update if needed.
- If R1 (automated) disagrees with R2 + R3 → update `scoring_evaluator.py` heuristic.
- If R2 (LLM) disagrees with R1 + R3 → update judge prompt; do not change scoring logic.

Disagreements are logged in `bench/synthesis_memos/ira_disputes.md`.

---

## Results

_TODO: Run protocol after dev.jsonl is populated (target: ≥150 tasks in dev partition)._

**Date run:** _TODO_
**Dev partition size:** _TODO_
**Sample size:** 50
**Overall κ (R1 vs R3):** _TODO_
**Pass criterion:** κ ≥ 0.75 overall, all dimensions ≥ 0.70
**Status:** ⏳ Pending
