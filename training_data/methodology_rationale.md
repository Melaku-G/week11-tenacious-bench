# Methodology Rationale — Path A (SFT)

**Author:** Melaku Y. · **Date:** 2026-05-01 · **Path:** A — Supervised Fine-Tuning

---

## Path Selection Justification

Week 10 traces show two dominant failure patterns in the unguarded baseline (~75% failure rate):

- **FC-3 (signal overclaim, ~40%)** — trace `b2c3d4e5-0001-4e5f-b001-day1base0p01x`: agent
  wrote "raised a Series B" and "scaling aggressively" for a prospect with `open_roles=0`
  and `layoff_event=True`. The model defaulted to optimistic SDR copy regardless of
  enrichment signal input.

- **FC-1 (hallucinated firmographics, ~30%)** — trace `b2c3d4e5-0002-4e5f-b001-day1base0p05x`:
  agent fabricated a funding round not present in the enrichment brief. Guardrail G5 (signal
  hedging rule) reduced this to ~15% but did not eliminate it.

- **FC-2 (segment-gate bypass, ~20%)** — trace `b2c3d4e5-0003-4e5f-b001-day1base0p13x`:
  agent pitched AI/LLM capabilities to a company with `ai_maturity_score=0`. Prompt-only
  guardrail (G3) reduced but did not eliminate paraphrase variants.

These are **generation-quality failures**: the model's output distribution defaults to
optimistic B2B copy regardless of input signals. Prompt engineering (Path B) reduces but
cannot fully retrain this prior; a reward model (Path C) adds evaluation overhead without
fixing the generative distribution. **SFT directly retrains the mapping from enrichment
signal → grounded output**, which is why Path A is the correct treatment.

---

## Design Choices and Paper Justifications

**1. Data volume (83 unique pairs → 1,016 weighted rows).**
Zhou et al. (2023) *LIMA*, §4 "Experiments" (Table 2, p.7): 1,000 carefully curated SFT
pairs suffice for instruction following on a 65B model (0.000015 pairs/param); quality
dominates quantity at every scale tested. Our 83 quality-filtered pairs at 1.5B scale give
0.000055 pairs/param — well above the LIMA ratio. Trace `b2c3d4e5-0001` (FC-3, open_roles=0,
layoff_event=True) and trace `b2c3d4e5-0002` (FC-1, hallucinated funding round) are both
signal-grounding failures that LIMA's quality-over-quantity principle directly addresses:
adding more weak examples would not have eliminated these failure modes; replacing them with
clean grounded pairs did. After per-source oversampling the training set reaches 1,016 rows,
within the 1,000–3,000 target range.

**2. Quality filter: score ≥ 0.75 with mandatory tone_compliance pass.**
The ≥ 0.75 threshold is the evaluator's own pass criterion — tasks that clear it are
judged acceptable by the same rubric used for held-out scoring. One additional hard gate is
applied: any task where tone_compliance = 0 (i.e. a banned phrase appears in the output) is
excluded regardless of overall score, because training on banned-phrase examples would
directly teach the model that Style Guide violations are acceptable. Of the 235 training
tasks, 45 fail tone_compliance; excluding them leaves 83 clean pairs. Tasks that fail other
dimensions (e.g. a missing hedge in a low-confidence brief) are retained because the
failure is conditional on a specific signal combination the model must learn to detect, not
a blanket style rule. This choice is directly motivated by trace `b2c3d4e5-0003` (FC-2):
the failure was a segment-gate bypass, not a tone violation — keeping borderline tasks for
those non-tone dimensions preserves the training signal for the harder conditional failures.

**3. Per-source oversampling (hand_authored 25×, trace_derived 20×, programmatic/synthesis 12×).**
Xu et al. (2024) *Magpie*, §3.3 "Difficulty-Aware Sampling": difficulty distribution
determines what a model learns from synthetic data; programmatic/template tasks compress the
difficulty distribution by over-representing easy surface patterns. Our programmatic tasks
(49 passing in train) are parameter sweeps with fixed templates — exactly the compression
Magpie §3.3 warns against. Hand-authored adversarial tasks (2 passing) and trace-derived
tasks (2 passing) represent the hard edge cases the model must generalise to; these map to
the "high-difficulty tail" Magpie recommends preserving. Oversampling 25× and 20×
respectively corrects for this compression; programmatic and synthesis tasks are
oversampled 12× to reach the 1,000-row floor without relying exclusively on easy examples.

**4. No DPO at this stage.**
Lambert et al. (2024) *Tülu 3*, §4.2 "Preference Tuning": DPO requires a reliable
preference judge (target agreement rate ≥ 85%, equivalent to Cohen's κ ≥ 0.70) to add
value over SFT; using a noisy judge introduces preference noise that degrades grounding
rather than improving it. Our LLaMA 3.1 8B judge achieved κ=0.04–0.26 on signal_fidelity
and format_compliance in IRA Round 2 — well below the Tülu 3 §4.2 threshold. The same
failure surfaces in trace `b2c3d4e5-0001` and `b2c3d4e5-0003`: a noisy judge would
generate conflicting preference labels for signal-overclaim emails, making the DPO gradient
signal unreliable. SFT only is the correct stage-one approach.

---

## Training Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Base model | Qwen2.5-1.5B-Instruct | Fits T4 (16 GB); instruction-tuned base avoids cold-start alignment |
| LoRA rank / alpha | 16 / 32 | Standard rank for domain adaptation; alpha=2× rank for stable updates |
| Max steps | 300 | LIMA finding: saturation reached early with high-quality data |
| Batch size | 4 (grad accum 4) | Effective batch = 16; balances memory and gradient stability on T4 |
| Learning rate | 2e-4 cosine | Unsloth default; cosine decay prevents overfitting to small dataset |
| Max seq len | 1024 | Enrichment brief + email fits comfortably; no truncation on any pair |

---

## Training Data Location

`bench/training_data/train_sft.jsonl` — 1,016 weighted rows from 83 unique pairs
(score ≥ 0.75, tone_compliance passes). Format: `conversations` array (system / user /
assistant) in ChatML style, compatible with Unsloth `SFTTrainer`. One JSON object per line.
