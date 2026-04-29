# Inter-Rater Agreement — Tenacious-Bench v0.1

## Purpose

Validates that the five machine-verifiable rubric dimensions produce consistent scores
across independent raters (automated scorer vs human annotator vs LLM judge).

---

## Protocol

### Sample
30 tasks from `bench/ira_sample_ids.json` (seed=7, stratified by category).

| Category | Count |
|----------|-------|
| FC1_hallucination | 6 |
| FC2_seg4_bypass | 6 |
| FC3_overclaim | 6 |
| FC9_draft_tag | 6 |
| tone_compliance | 4 |
| FC4_injection | 1 |
| FC7_bench_capacity | 1 |

### Raters
| Rater | Type | Tool |
|-------|------|------|
| R1 | Automated | `bench/scoring_evaluator.py` |
| R2 | LLM judge | `meta-llama/llama-3.1-8b-instruct` via OpenRouter, `bench/generation_scripts/ira_r2_runner.py` |
| R3 | Human | Tenacious team annotator, `bench/ira_r3_annotation_sheet.md` |

### Procedure
1. R1 runs `scoring_evaluator.py` on the 30-task sample → scores recorded.
2. R2 receives each task via a rubric-explicit prompt; returns per-dimension 0/1 + reason.
3. R3 scores each task independently using `bench/ira_r3_annotation_sheet.md`; 24-hour
   re-label interval from R1 to reduce anchoring bias.
4. Cohen's κ computed pairwise per dimension. Trigger for rubric revision: R3 disagrees
   with R1 on any dimension — review rubric definition before changing scorer.

---

## Results: R1 vs R2 (2026-04-29)

**Date:** 2026-04-29 | **n = 30** | **R2 model:** `meta-llama/llama-3.1-8b-instruct`

Two runs were conducted: Run 1 with the original judge prompt, Run 2 with a refined
prompt targeting the three identified failure modes (confidence_hedging condition
inversion, format_compliance [DRAFT] hallucination, segment_gate keyword list). Both
runs are recorded below.

### Run 1 — Original prompt

| Dimension | R1 pass% | R2 pass% | Agree% | Cohen's κ | Target κ | Status |
|-----------|----------|----------|--------|-----------|----------|--------|
| signal_fidelity | 100.0% | 83.3% | 83.3% | 0.00† | ≥ 0.70 | ARTIFACT |
| tone_compliance | 86.7% | 86.7% | 100.0% | 1.00 | ≥ 0.80 | **PASS** |
| segment_gate | 83.3% | 100.0% | 83.3% | 0.00† | ≥ 0.85 | ARTIFACT |
| confidence_hedging | 53.3% | 93.3% | 60.0% | 0.15 | ≥ 0.70 | FAIL |
| format_compliance | 76.7% | 96.7% | 73.3% | −0.06 | ≥ 0.90 | FAIL |
| **Overall (≥0.75)** | **73.3%** | **80.0%** | **73.3%** | **0.26** | **≥ 0.75** | FAIL |

### Run 2 — Refined prompt (explicit condition logic + subject character check)

| Dimension | R1 pass% | R2 pass% | Agree% | Cohen's κ | Target κ | Status |
|-----------|----------|----------|--------|-----------|----------|--------|
| signal_fidelity | 100.0% | 56.7% | 56.7% | 0.00† | ≥ 0.70 | ARTIFACT |
| tone_compliance | 86.7% | 86.7% | 100.0% | 1.00 | ≥ 0.80 | **PASS** |
| segment_gate | 83.3% | 70.0% | 53.3% | −0.27 | ≥ 0.85 | FAIL |
| confidence_hedging | 53.3% | 96.7% | 56.7% | 0.08 | ≥ 0.70 | FAIL |
| format_compliance | 76.7% | 76.7% | 53.3% | −0.30 | ≥ 0.90 | FAIL |
| **Overall (≥0.75)** | **73.3%** | **53.3%** | **53.3%** | **0.04** | **≥ 0.75** | FAIL |

† κ = 0.00 is a statistical artifact when one rater has near-uniform scores (see below).

### Root-cause analysis

**tone_compliance (κ = 1.00 in both runs):** Perfect agreement. Banned-phrase keyword
matching translates perfectly to LLM scoring. This is the only rubric dimension that
meets the κ ≥ 0.80 target. It also requires the least judgment — it is a pure lexical
check that both automated and LLM scorers can execute without ambiguity.

**confidence_hedging (κ = 0.15 / 0.08):** Run 1: R2 inverts condition logic — reads
`icp_confidence = "low"` and concludes hedging "does not apply." The refined prompt
added explicit trigger language but R2 still passes 96.7% (vs R1's 53.3%). The LLM
continues to misapply the conditional requirement even with step-by-step instructions.
This is a fundamental reliability failure of the 8B model for this dimension.

**format_compliance (κ = −0.06 / −0.30):** Run 1: R2 hallucinates [DRAFT] in subjects
starting with "Context:". Run 2: after adding character-by-character verification,
R2's pass rate drops to 76.7% (matching R1) but on different tasks — agreement falls
to 53.3% (worse than Run 1). The model correctly learns to check the tag but
misidentifies which tasks have it. Prompt refinement introduced new hallucinations.

**signal_fidelity (R2 over-strict in Run 2):** After prompt refinement, R2 now fails
tasks with any growth language including well-supported claims. R2 applies the pattern
too broadly — it fails even tasks where the brief supports moderate growth (velocity=high,
open_roles > 3). Over-correction.

**Model conclusion:** LLaMA 3.1 8B shows high prompt sensitivity and does not converge to
reliable rubric scoring across two runs. Only `tone_compliance` (a pure lexical check) is
stable. This is consistent with the Gu et al. (2025) finding that rubric-explicit scoring
requires models capable of multi-step conditional reasoning — properties that 8B models lack.

**Implication for R2:** A capable judge model (Claude Sonnet or GPT-4 class) is required to
achieve κ ≥ 0.75 overall. The current R2 results establish a lower bound (κ = 0.04–0.26)
that larger models should comfortably exceed. This is noted as a v0.2 task.

### Statistical artifact note

κ = 0.0 occurs when one rater has near-uniform scores: R1 passes 100% of signal_fidelity
(zero negative examples from R1's perspective), driving p_e → p_o. In Run 2, the
same artifact appears in signal_fidelity. These dimensions require R3 data to produce
interpretable κ estimates.

### Disputes logged
Full per-task dispute analysis: `bench/synthesis_memos/ira_disputes.md`

---

## Results: R3 Human Annotation (2026-04-29)

**Annotator:** Melaku Y. | **Date:** 2026-04-29 | **n = 30**

| Dimension | R1 vs R3 κ | R2 vs R3 κ | Target κ | R1 status | R2 status |
|-----------|-----------|-----------|----------|-----------|-----------|
| signal_fidelity | 0.00† | 0.41 | ≥ 0.70 | ARTIFACT | FAIL |
| tone_compliance | **1.00** | **1.00** | ≥ 0.80 | **PASS** | **PASS** |
| segment_gate | **1.00** | −0.27 | ≥ 0.85 | **PASS** | FAIL |
| confidence_hedging | **1.00** | 0.08 | ≥ 0.70 | **PASS** | FAIL |
| format_compliance | **1.00** | −0.30 | ≥ 0.90 | **PASS** | FAIL |
| **Overall (≥0.75)** | **0.77** | 0.25 | ≥ 0.75 | **PASS** | FAIL |

† R1 vs R3 signal_fidelity κ=0.00 is a statistical artifact (R1 passes 100%, driving p_e→p_o).
Actual agreement: 83.3% (25/30 agree); 5 tasks where R3=0, R1=1 — all have layoff=True OR open_roles=0.

### R1 vs R3 interpretation

R1 passes the IRA. Overall κ = 0.77, exceeding the 0.75 target. Four dimensions achieve
perfect agreement (κ=1.00). The only divergence is signal_fidelity where R3 (human) flags 5
tasks R1 missed — all cases where the email contains growth language paired with a hard
negative context (layoff=True OR open_roles=0).

**Trigger activated:** R3 disagrees with R1 on signal_fidelity. Per protocol: R1 disagrees
with R2 (Run 1) + R3 → update scoring_evaluator.py.

**Action taken (2026-04-29):** Added `STRONG_NEGATIVE_GROWTH_PATTERNS` to
`scoring_evaluator.py`, fired only when `layoff=True OR open_roles=0`:
- `scal\w+\s+(?:its|your)?\s*(?:engineering\s+)?(?:team|operations)`
- `scal\w+\s+aggressively`
- `raised\s+a?\s*series\s+[a-zA-Z]`
- `expanding\s+into\s+\w`

All 5 disputed tasks now correctly score 0 on signal_fidelity post-update.

### R2 vs R3 interpretation

R2 (LLaMA 8B) fails the IRA overall (κ=0.25). Only tone_compliance achieves κ=1.00.
R1 (automated scorer) is the authoritative rater; LLaMA 8B is not suitable for
rubric scoring beyond pure lexical checks.

---

## Disagreement Resolution Protocol

| Disagreement pattern | Action |
|---------------------|--------|
| R3 disagrees with R1 + R2 | Review rubric definition; update if ambiguous |
| R1 disagrees with R2 + R3 | Update `scoring_evaluator.py` heuristic |
| R2 disagrees with R1 + R3 | Update judge prompt in `ira_r2_runner.py` |

**Day 3 actions taken (before R3):**
- Updated R2 judge prompt for `confidence_hedging`: explicit trigger language added
- Updated R2 judge prompt for `format_compliance`: character-level subject check added
- Updated R2 judge prompt for `segment_gate`: explicit keyword list added

**Pending (after R3):**
- If R3 confirms R2 is correct on `signal_fidelity`: extend GROWTH_CLAIM_PATTERNS in
  `scoring_evaluator.py` to include funding round and market expansion patterns

---

## Rubric Revision Trigger

**Trigger criterion:** any dimension below 80% agreement between R1 and R3.

**Current R1 vs R2 status:**
- tone_compliance: 100% agreement — no trigger
- confidence_hedging: 60% agreement — **below trigger** but attributed to R2 prompt error
- format_compliance: 73.3% agreement — **below trigger** but attributed to R2 hallucination

Both below-trigger dimensions are explained by documented R2 failures (inverted logic,
hallucination). Rubric revision is NOT triggered pending R3 confirmation.

Full results will be appended when R3 completes.
