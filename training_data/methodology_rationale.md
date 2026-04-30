# Methodology Rationale — Path A (SFT)

**Author:** Melaku Y. · **Date:** 2026-04-29 · **Path:** A — Supervised Fine-Tuning

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

**1. Data volume (25 pairs → 48 weighted) is sufficient.**
Zhou et al. (2023) *LIMA* show that 1,000 carefully curated SFT pairs suffice for
instruction following on a 65B model (0.000015 pairs/param). Our 27 violation-free pairs
at 1.5B scale give 0.000018 pairs/param — comparable ratio. Every pair scores exactly
1.0 on the deterministic rubric scorer (no failing dimension, no LLM in the loop).
Quality over quantity is the operative principle at this domain-specific scale.

**2. Per-source oversampling (hand_authored 4×, trace_derived 2×).**
Xu et al. (2024) *Magpie* show that difficulty distribution determines what a model
learns from synthetic data. Programmatic tasks (150 in train) are parameter sweeps with
fixed templates — they compress the difficulty distribution. Hand-authored adversarial
tasks (21 in train)
the model must generalise to. Oversampling 4× and 2× respectively corrects for this
compression without requiring more generation budget.

**3. No DPO at this stage.**
Lambert et al. (2024) *Tülu 3* require a high-quality preference judge for DPO to add
value over SFT. Our LLaMA 3.1 8B judge achieved κ=0.04–0.26 on signal_fidelity and
format_compliance in IRA Round 2 — well below the ≥0.70 threshold for reliable
preference labelling. Adding DPO with a noisy judge risks introducing preference noise
that degrades grounding. SFT only is the correct stage-one approach.

**4. Score filter == 1.0 (all dimensions pass — no violations).**
The ≥ 0.75 rubric pass threshold is designed for evaluation, not training data selection.
Because no single dimension weight exceeds 0.25, a task can score 0.80 with one failing
dimension (e.g. a banned phrase in tone_compliance, weight=0.20). Of the 235 training
tasks, 108 score 0.75–0.99 but contain at least one rubric violation. Training on those
as positive examples would teach the model that violations are acceptable.
The correct filter is score == 1.0: every dimension either passes or returns n/a (hedging
not required). This yields 27 clean pairs → 52 weighted rows after source oversampling.
LIMA (Zhou et al. 2023) confirms that data quality dominates quantity at this scale.

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

`bench/training_data/train_sft.jsonl` — 52 weighted rows from 27 unique clean pairs
(score == 1.0, no failing dimension). Format: `conversations` array (system / user /
assistant) in ChatML style, compatible with Unsloth `SFTTrainer`. One JSON object per line.
