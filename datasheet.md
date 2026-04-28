# Datasheet for Tenacious-Bench v0.1

_Following Gebru et al. (2021) "Datasheets for Datasets" framework, extended with Pushkarna et al. (FAccT 2022) layered documentation structure._

---

## Executive Summary (Telescopic View)
_Pushkarna et al. (FAccT 2022) — Layer 1: one-paragraph overview for any reader._

Tenacious-Bench v0.1 is a 300-task evaluation benchmark for B2B sales outreach agents in the Tenacious Consulting & Outsourcing conversion engine. It was built because general-purpose benchmarks (tau2-Bench retail, HELM, MTEB) cannot detect the six failure classes that cause real brand and legal risk in outbound SDR automation: signal overclaiming, segment gate bypass, tone guide violation, confidence hedging omission, contact-role mismatch, and prompt injection via enrichment fields. The benchmark grades every task on five machine-verifiable rubric dimensions (signal fidelity, tone compliance, segment gate, confidence hedging, format compliance) and returns a weighted score between 0 and 1; pass threshold is 0.75. What this benchmark **cannot** grade: general LLM reasoning quality, factual QA accuracy, customer service task resolution, multi-turn dialogue coherence, or any outreach domain outside B2B engineering staffing. Do not apply it to evaluate general-purpose language models or non-Tenacious outreach contexts.

---

---

## Periscopic View — Process and Provenance
_Pushkarna et al. (FAccT 2022) — Layer 2: mid-detail for practitioners integrating the dataset._

**Why this benchmark was built:** tau2-Bench retail grades binary task completion against
a generic retail policy document. It has no mechanism to check whether an outreach email
correctly grounds claims in a supplied enrichment brief, respects a brand tone guide, or
applies segment-specific pitch gates. Six specific failure classes identified in Week 10
probing (FC-1 through FC-7) are invisible to tau2-Bench — see `bench/audit_memo.md`.

**Who made key decisions:**
- Rubric dimensions and weights: authored by the Tenacious conversion-engine team based on
  the brand guide, failure taxonomy (`probes/failure_taxonomy.md`), and Week 10 probe results.
- Held-out sealing: automated immediately after programmatic generation on 2026-04-27.
  No human reviewed held-out tasks prior to sealing.
- Judge rotation policy: DeepSeek generates, Qwen judges — enforced at runtime in
  `synthesis.py` to prevent preference leakage (Li et al., 2025).

**Key design choices and their rationale:**

| Choice | Decision | Reason |
|--------|----------|--------|
| Binary rubric (0/1 per dimension) | Machine-verifiable, no partial credit | Liu et al. (2024): verifiable criteria produce stronger SFT signal |
| Four authoring modes | Trace-derived + programmatic + synthesis + hand-authored | Diversity of failure surface; reduces mode-specific overfitting |
| Programmatic failure injection | Templates per failure class | Ensures every failure mode has ≥30 training examples |
| Pass threshold 0.75 | Weighted sum across 5 dimensions | Allows one minor fail (e.g. hedging) while requiring core signal/tone compliance |
| Held-out 20% sealed | Single-use for final ablation | Prevents target leakage during hyperparameter search |

**What the dataset cannot do:** grade general LLM quality, evaluate multi-turn dialogue,
test factual QA, or assess outreach for non-engineering staffing domains.

---

## Microscopic View — Full Technical Specification
_Pushkarna et al. (FAccT 2022) — Layer 3: reproduction-grade detail._

Full field specification: `bench/schema.json` (task schema + 3 worked examples).
Contamination check results: `bench/contamination_check.json` (5 checks, CC-004 clean).
Generation script hashes and parameters: see `generation_scripts/` — each script is
deterministic given `--seed`. Canonical seeds: programmatic train=42, dev=43, held_out=44;
synthesis seed=99.

**Partition counts by source mode (as of 2026-04-28):**

| Mode | train | dev | held_out | Total |
|------|-------|-----|----------|-------|
| programmatic | 150 | 90 | 60 | 300 |
| trace_derived | 2 | 2 | 1 | 5 |
| synthesis | 62 | 12 | 0 | 74 |
| hand_authored | 3 | 1 | 1 | 5 |
| **Total** | **217** | **105** | **62** | **384** |

**Scoring evaluator:** `bench/scoring_evaluator.py` — regex + keyword matching, no LLM
calls, deterministic. Mean scores (all sources): train 0.872, dev 0.836, held_out 0.799.
Pass rate (score ≥ 0.75): train 85.7%, dev 77.1%, held_out 67.7%.

---

## 1. Motivation

**For what purpose was the dataset created?**
Tenacious-Bench v0.1 was created to evaluate whether a B2B sales outreach agent correctly grounds
its copy in enrichment signals, respects segment-specific pitch gates, follows a brand tone guide,
and applies appropriate hedging under data uncertainty. Standard benchmarks (tau2-Bench retail,
MTEB, HELM) do not test these dimensions.

**Who created the dataset and on behalf of whom?**
Created by the Tenacious conversion-engine team as part of the Week 11 challenge deliverable.

**Was there specific funding?**
No external funding. Compute costs: ~$0 (programmatic generation) + <$2 (LLM synthesis via OpenRouter).

---

## 2. Composition

**What do the instances represent?**
Each instance is a single evaluation task: an enrichment signal brief (company + firmographics +
ICP segment + confidence) paired with a candidate email output and a rubric specifying the
correct behaviour.

**How many instances?**
384 tasks: train 217 (56%), dev 105 (27%), held-out 62 (16%). The original programmatic
generation produced 300 tasks; synthesis (74 tasks) and trace/hand-authored (10 tasks)
expanded the total.

**What data does each instance contain?**
- `input`: company, domain, warm flag, contact_name, contact_role, enrichment_brief, system_prompt_excerpt
- `candidate_output`: email_subject, email_body, optional tool_calls
- `ground_truth`: expected_behaviour (natural language) + passing_conditions (machine-verifiable)
- `rubric`: five dimension objects with weights and scoring criteria
- `score`: weighted rubric sum (null before scoring)

**Is there a label or target associated with each instance?**
Yes — the `score` field (0.0–1.0) and per-dimension binary scores in `dimension_scores`.

**Are there recommended data splits?**
Train: `bench/tenacious_bench_v0.1/train.jsonl`
Dev: `bench/tenacious_bench_v0.1/dev.jsonl`
Held-out: `bench/tenacious_bench_v0.1/held_out.jsonl` (sealed — not to be used during training)

---

## 3. Collection Process

**How was the data acquired?**

| Mode | Share | Method |
|------|-------|--------|
| Trace-derived | ~30% | `eval/trace_log.jsonl` restructured into (input, candidate, rubric) |
| Programmatic | ~30% | Probe library parameter sweeps (see `generation_scripts/programmatic.py`) |
| Multi-LLM synthesis | ~25% | OpenRouter cheap tier, judge-filtered (see `generation_scripts/synthesis.py`) |
| Hand-authored adversarial | ~15% | Written to defeat the Week 10 agent on edge cases |

**Who was involved in data collection?**
Automated pipeline (trace_derived, programmatic, synthesis) + human authoring (adversarial).

**Over what timeframe was data collected?**
Week 10 traces: April 22–27, 2026. Programmatic/synthesis/adversarial: April 27–29, 2026.

---

## 4. Preprocessing / Cleaning / Labeling

**Was any preprocessing done?**
- LLM-as-judge quality filter: all synthesis and programmatic tasks scored on `input_coherence`,
  `ground_truth_verifiability`, `rubric_clarity` (1–5). Tasks with any dimension < 3 are excluded.
- Contamination check: N-gram overlap (<8-gram overlap with held-out) + embedding similarity
  (<0.85 cosine) via `bench/contamination_check.json`.
- Deduplication: tasks with identical `input.enrichment_brief` hash removed.

**Is the software used to preprocess available?**
Yes — `bench/scoring_evaluator.py` (machine-verifiable scoring) and `bench/generation_scripts/`.

---

## 5. Uses

**Has the dataset been used for any tasks already?**
Used for evaluating the Week 10 Tenacious conversion engine agent. Baseline numbers:
- Unguarded: ~75% of prospects triggered ≥1 failure class
- Guarded: ~30% residual (primarily FC-1 and FC-3 paraphrase variants)

**What are the intended uses?**
1. Ablation evaluation during SFT training (dev partition)
2. Final model evaluation (held-out partition, single use)
3. Regression testing after agent updates

**Are there uses that should be avoided?**
- Do not use held-out partition for training data selection or hyperparameter tuning.
- Do not report held-out scores as interim benchmark numbers — reserve for final ablation only.

---

## 6. Distribution

**How will the dataset be distributed?**
Within the `conversion-engine` repository. Held-out partition intentionally excluded from
public distribution to prevent contamination.

**Are there export controls or other regulatory restrictions?**
No PII in the dataset. All company names are synthetic or publicly available Crunchbase entries.

---

## 7. Maintenance

**Who is maintaining the dataset?**
Tenacious conversion-engine team.

**How can errors be reported?**
Open an issue in the `conversion-engine` repository with label `bench-error`.

**Will the dataset be updated?**
Version 0.2 planned after Week 11 challenge completion. Updates will increment the version
number and re-run contamination checks against all prior versions.

---

## 8. Lifecycle Events (Pushkarna et al. 2022)

_This section records decisions already made, following Pushkarna et al.'s recommendation that
dataset documentation should track historical events, not only forward-looking maintenance plans._

| Date | Event | Detail |
|------|-------|--------|
| 2026-04-22 | Week 10 traces collected | 5 trace IDs from `day1_baseline` condition; used as ground truth for trace-derived partition |
| 2026-04-27 | v0.1 dataset generation | Programmatic script run: train (90 tasks, seed=42), dev (45 tasks, seed=43), held_out (seed=44) |
| 2026-04-27 | Held-out partition sealed | `bench/tenacious_bench_v0.1/held_out.jsonl` — 80 tasks. Sealed post-generation. Must not be used for training, hyperparameter tuning, or interim evaluation. Reserved for final Day 6 ablation only. |
| 2026-04-27 | Contamination check | Pending — `bench/contamination_check.json` target: n-gram <8-gram overlap, cosine <0.85 |
| 2026-04-27 | Schema v0.1 finalised | `bench/schema.json` with pass_threshold=0.75, five rubric dimensions, three worked examples |
| 2026-04-27 | Scoring evaluator v0.1 | `bench/scoring_evaluator.py` — machine-verifiable, regex-based, no LLM calls required |
| — | IRA protocol run | Target: κ ≥ 0.75 on 30-task sample; 24-hour re-label interval (see `bench/inter_rater_agreement.md`) |
| — | v0.2 planned | Post-Week 11 completion; will include synthesis.py tasks (requires OPENROUTER_API_KEY) |

_Pending dates will be filled in when those events occur. Completed events are immutable — do not
edit them to reflect revised decisions; instead, add a new row with the correction and the date._
