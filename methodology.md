# Methodology — Tenacious-Bench v0.1

## Path Declaration

**Selected path: A — Supervised Fine-Tuning of a Generation Component**

Committed: 2026-04-27

### Justification

The dominant failure modes observed in Week 10 are generation-quality failures, not
inconsistency or trajectory failures:

- **FC-3 Over-claim on hiring signals** (~40% unguarded trigger rate): the agent produces
  outreach copy that asserts growth or scaling when enrichment data shows the opposite.
  This is a generation failure — the model defaults to optimistic SDR copy from its
  training distribution regardless of what the signal brief says.

- **FC-1 Hallucinated firmographics** (~30% when no CSV match): the agent fills missing
  enrichment data with plausible-sounding but fabricated facts. Again a generation failure
  — the model generates fluent, confident text even when it has no evidence to draw on.

Both failures are best addressed by SFT on grounded (input, correct-output) pairs drawn
from traces where the agent behaved correctly, contrasted against traces where it failed.
A preference-tuned judge (Path B) would detect these failures but not fix the generation.
A process reward model (Path C) is over-engineered for failures that occur in a single
generation step, not across a trajectory.

### Supporting trace IDs

FC-3 over-claim (P01, unguarded baseline):
- Trace ID: `b2c3d4e5-0001-4e5f-b001-day1base0p01x`
- Failure: agent wrote "as your engineering team continues to scale rapidly" despite
  `open_roles_estimate=1` and `engineering_velocity=low`

FC-2 segment gate bypass (P05, unguarded baseline):
- Trace ID: `b2c3d4e5-0002-4e5f-b001-day1base0p05x`
- Failure: agent sent AI capability gap pitch referencing "ML infrastructure gaps" to
  company with `ai_maturity_score=0` (threshold: ≥2 required)

FC-2 is included as secondary evidence that generation failures extend beyond over-claiming —
the model ignores structured signal fields (`ai_maturity_score`) in the same way it ignores
velocity signals in FC-3. Both are the same root cause: the model does not attend to
conditional constraints from the enrichment brief.

Both from `probes/held_out_traces.jsonl`, condition `day1_baseline`, guardrails_active=[].

### Training target

Qwen 3.5 2B with LoRA (rank 16, alpha 32), trained on signal-grounded (input, output)
pairs from the training partition of Tenacious-Bench v0.1. Target: agent produces
hedged, evidence-anchored copy when hiring signal is low, without being prompted
explicitly.

---

## Benchmark Design Rationale

### Why tau2-Bench retail does not cover Tenacious-specific behaviour

tau2-Bench retail tests multi-turn customer service resolution against a retail policy
document. It does not test:

1. Whether an outreach email over-claims on a hiring signal
2. Whether enrichment data is faithfully used vs ignored in copy
3. Whether the Tenacious tone guide is followed (Direct, Grounded, Honest, Professional,
   Non-condescending)
4. Whether segment-specific pitches are suppressed when ICP confidence is low
5. Whether competitor gap data is hedged when peer count is < 5

Tenacious-Bench v0.1 grades all five. See `audit_memo.md` for full gap analysis.

### Dataset construction approach

| Mode | Target share | Source |
|------|-------------|--------|
| Trace-derived | ~30% | eval/trace_log.jsonl restructured into (input, candidate, rubric) |
| Programmatic | ~30% | probe_library.md probes expanded with parameter sweeps |
| Multi-LLM synthesis | ~25% | OpenRouter cheap tier, judge-filtered |
| Hand-authored adversarial | ~15% | Written to defeat the Week 10 agent on edge cases |

### Partitioning

| Partition | Share | File | Use |
|-----------|-------|------|-----|
| Training | 50% | train.jsonl | SFT training data |
| Dev | 30% | dev.jsonl | Iteration during authoring |
| Held-out | 20% | held_out.jsonl | Sealed — final ablation only |

---

## Judge Rotation Policy

For multi-LLM synthesis tasks, the generation model and judge model must be from different
model families. Using the same family for both creates preference leakage — the judge
favours outputs from its own training distribution, inflating pass rates.

| Role | Model | Family |
|------|-------|--------|
| Generation | `deepseek/deepseek-chat` | DeepSeek |
| Judge | `meta-llama/llama-3.1-8b-instruct` | Meta LLaMA |

_Note: original judge was `qwen/qwen-2.5-72b-instruct` but the Qwen model was routed by
OpenRouter to the Novita provider which returned 400 "does not support endpoint: completions".
Switched to LLaMA 3.1 8B, which is a different family from DeepSeek and satisfies the
preference-leakage constraint._

Per Li et al. (2025). Enforced at runtime: `synthesis.py` raises `SystemExit` if
`--model` and `--judge-model` resolve to the same value.

---

## Inter-Rater Agreement

**Protocol:** 30-task stratified sample from dev partition (6 per category where available),
scored by three raters: R1 (automated scorer), R2 (LLM judge), R3 (human annotator).
R1 is deterministic. R3 requires a 24-hour re-label interval to reduce anchoring bias.
Trigger for rubric revision: any dimension below 80% agreement between R1 and R3.

**Sample selection:** `bench/ira_sample_ids.json` — 30 tasks, seed=7, stratified by category.

**R1 results (automated scorer, 2026-04-28, n=30):**

| Dimension | Pass rate | Pass count |
|-----------|-----------|------------|
| signal_fidelity | 100.0% | 30/30 |
| tone_compliance | 86.7% | 26/30 |
| segment_gate | 83.3% | 25/30 |
| confidence_hedging | 50.0% | 15/30 |
| format_compliance | 76.7% | 23/30 |
| **Overall (score ≥ 0.75)** | **76.7%** | **23/30** |

**R2 results (LLM judge, meta-llama/llama-3.1-8b-instruct, 2026-04-29, n=30):**

Two runs conducted (original prompt; refined prompt with explicit condition logic).
Best summary: tone_compliance achieves κ=1.00 in both runs; all other dimensions fail.

| Dimension | R1 pass% | Run 1 κ | Run 2 κ | Target | Notes |
|-----------|----------|---------|---------|--------|-------|
| signal_fidelity | 100.0% | 0.00† | 0.00† | ≥ 0.70 | Artifact; R1 uniform |
| tone_compliance | 86.7% | **1.00** | **1.00** | ≥ 0.80 | Only stable dimension |
| segment_gate | 83.3% | 0.00† | −0.27 | ≥ 0.85 | R2 unreliable |
| confidence_hedging | 53.3% | 0.15 | 0.08 | ≥ 0.70 | R2 inverts condition logic |
| format_compliance | 76.7% | −0.06 | −0.30 | ≥ 0.90 | R2 hallucinates [DRAFT] |
| **Overall** | 73.3% | 0.26 | 0.04 | ≥ 0.75 | Neither run meets target |

†kappa=0.00 is a statistical artifact (near-uniform R1 scores).

**Key finding:** LLaMA 3.1 8B is prompt-sensitive and cannot reliably apply multi-step
conditional rubric criteria. `tone_compliance` (pure lexical check) is the only dimension
reproducible by the LLM judge. For R2 to meet κ targets, a Claude Sonnet or GPT-4 class
model is required. This is a v0.2 task.

**`signal_fidelity` secondary finding:** Run 1 R2 detected 5 failures R1 misses — emails
claiming "raised a Series B" when brief has open_roles=0. R1's GROWTH_CLAIM_PATTERNS
lacks funding-claim patterns. Pending R3 adjudication before scorer update.

**R3 results (human annotator, Melaku Y., 2026-04-29, n=30):**

| Dimension | R1 vs R3 κ | R2 vs R3 κ | Target | R1 status |
|-----------|-----------|-----------|--------|-----------|
| signal_fidelity | 0.00† | 0.41 | ≥ 0.70 | ARTIFACT |
| tone_compliance | **1.00** | **1.00** | ≥ 0.80 | **PASS** |
| segment_gate | **1.00** | −0.27 | ≥ 0.85 | **PASS** |
| confidence_hedging | **1.00** | 0.08 | ≥ 0.70 | **PASS** |
| format_compliance | **1.00** | −0.30 | ≥ 0.90 | **PASS** |
| **Overall (≥0.75)** | **0.77** | 0.25 | ≥ 0.75 | **PASS** |

† κ=0.00 is a statistical artifact (R1 uniform 100% on signal_fidelity). Actual R1 vs R3
agreement: 83.3%, with 5 tasks where R3 correctly flagged R1 misses (see below).

**R1 IRA status: PASS** (overall κ=0.77, target ≥ 0.75).

**Signal_fidelity rubric update (triggered by R3):** R3 disagrees with R1 on 5 tasks — all
emails containing growth claims (raised a Series B, scale operations, scaling aggressively)
paired with `layoff=True OR open_roles=0`. R1 was under-specified. Per IRA protocol
(R1 disagrees with R2+R3 → update scorer):

Added `STRONG_NEGATIVE_GROWTH_PATTERNS` to `scoring_evaluator.py`, fired only when
`layoff=True OR open_roles=0`. All 5 disputed tasks now score 0 on signal_fidelity.
Updated partition scores: train mean=0.783, dev mean=0.747, held_out mean=0.732.

Full results: `bench/ira_kappa_final.json`.

**Post-revision R1 vs R3 agreement (after scorer fix, 2026-04-29):**

| Dimension | Pre-fix R1 vs R3 κ | Post-fix R1 vs R3 κ | Change | Target | Final Status |
|-----------|-------------------|--------------------|----|--------|------|
| signal_fidelity | 0.00† (artifact) | **1.00** | +1.00 | ≥ 0.70 | **PASS** |
| tone_compliance | 1.00 | 1.00 | 0.00 | ≥ 0.80 | **PASS** |
| segment_gate | 1.00 | 1.00 | 0.00 | ≥ 0.85 | **PASS** |
| confidence_hedging | 1.00 | 1.00 | 0.00 | ≥ 0.70 | **PASS** |
| format_compliance | 1.00 | 1.00 | 0.00 | ≥ 0.90 | **PASS** |
| **Overall** | **0.77** | **1.00** | +0.23 | ≥ 0.75 | **PASS** |

Post-fix: R1 and R3 now agree on all 30 IRA sample tasks. The 5 previously disputed tasks
(signal_fidelity false negatives) are all correctly scored 0 by the updated scorer.
The scorer update is the only change — no task labels, partition assignments, or rubric
weights were modified. IRA round is closed.

---

## Contamination Check Protocol

Three checks run before held-out is sealed:

1. **N-gram overlap** — no exact 8-gram match between train/dev inputs and held-out inputs
2. **Embedding similarity** — cosine similarity < 0.85 (all-MiniLM-L6-v2) between any
   train/dev `email_body` and any held-out `email_body`
3. **Time-shift verification** — held-out tasks authored after the last train/dev task;
   any task referencing public signal data (e.g. company names from Crunchbase) is
   date-stamped to confirm it was not present in the training window

Results logged in `bench/contamination_check.json`. Any flagged task is removed from
the relevant partition before sealing.

---

## Contingency: What If SFT Does Not Improve Delta B?

The Path A bet is that FC-3 and FC-1 are generation failures addressable by SFT. The
honest failure mode for this choice:

**If held-out Delta B (SFT vs guarded prompt-only) ≤ 0:** the model memorised surface
patterns in the training pairs but did not generalise the grounding behaviour to
out-of-distribution probes in held-out.

Contingency options, in order of preference:
1. Expand training set with harder adversarial pairs (currently 15% → increase to 30%)
   targeting the specific paraphrase variants the model failed on
2. Add Path B judge as a post-generation filter (does not require retraining; can be
   deployed in 1 day as a classifier on candidate outputs)
3. Hybrid: keep SFT adapter for signal-fidelity improvement; add judge for tone/hedging

The contingency is not a fallback from Path A — it is the expected iteration cycle.
Path A is the primary training target; Path B is the safety net if generation alone
is insufficient.
