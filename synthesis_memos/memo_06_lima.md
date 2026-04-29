# Memo 06 — LIMA: Less Is More for Alignment

**Citation:** Zhou et al. (2023). *LIMA: Less Is More for Alignment.* NeurIPS 2023.

**Path relevance:** Path A — Supervised Fine-Tuning of a Generation Component

---

## Core Claim

LIMA demonstrates that **1,000 carefully curated instruction-response pairs are sufficient to align a pretrained LLM** (LLaMA 65B) to competitive instruction-following quality — matching or exceeding models trained on 52K FLAN examples. The central finding: alignment is a shallow skill. The model already encodes domain knowledge from pretraining; SFT teaches the *format and style* of responses, not the underlying competence.

---

## Methods Summary

1. **Dataset curation** — 1,000 examples hand-curated from Stack Exchange (high-quality Q&A), wikiHow, Super-NaturalInstructions, and 200 hand-authored examples.
2. **Quality bar** — Annotators selected examples for clarity, depth, diversity of style, and zero hallucination. No data augmentation. No filtering pipeline.
3. **Training** — Standard SFT on LLaMA 65B, 15 epochs, cosine LR schedule. No RLHF, no DPO, no reward model.
4. **Evaluation** — GPT-4 as judge on head-to-head comparisons vs Alpaca (52K examples), OpenAI Davinci-003 (RLHF). Human raters preferred LIMA outputs in 50% of cases vs DaVinci-003 — competitive despite 52× fewer training examples.
5. **Consistency hypothesis** — A small number of high-quality examples with consistent format and style is more important than volume.

---

## Why This Supports Path A for Tenacious-Bench

The Tenacious training partition has 217 tasks. The LIMA result validates this scale. The IRA pass rate is 61.3% (mean score 0.783), meaning ~133 tasks pass the 0.75 threshold — within the LIMA 1K range and directionally consistent with their "small set, high quality" finding.

The specific FC-3 failure (over-claiming on low signals) is a **format and style failure**, not a knowledge failure — exactly the alignment type LIMA addresses. The model knows what enrichment signals mean; it defaults to optimistic SDR copy because that style dominated pretraining. LIMA-style SFT on grounded Tenacious pairs teaches the output *format* (hedged, evidence-anchored) without requiring large volumes.

---

## One Disagreement

Zhou et al. argue that diversity of style across 1,000 examples is the primary driver of alignment quality — each example should demonstrate a distinct response pattern. For Tenacious-Bench, the training partition is **intentionally clustered by failure class** (≥30 examples per failure mode per the benchmark design spec). This means many examples share very similar input structures (same company type, same failure trigger).

**Disagreement:** LIMA's diversity hypothesis does not translate cleanly to domain-specific failure correction. For Tenacious-Bench, failure-class concentration is correct — the model needs to see FC-3 (over-claim with low open_roles) many times to change the generation behavior for that specific condition. Style diversity is secondary when the goal is to fix a specific distributional failure mode rather than broad instruction following. The IRA R1 result (61.3% pass on diverse partition) confirms the training set produces sufficient signal at this scale without needing to enforce diversity constraints.

---

## Implications for Tenacious-Bench Training

| LIMA Finding | Tenacious-Bench Application |
|-------------|---------------------------|
| 1K high-quality > 52K noisy | 133 high-pass tasks (score≥0.75) is a workable training set |
| Alignment is a shallow skill — format/style, not knowledge | SFT teaches "hedge in this context" as a format pattern |
| Consistency of output format matters more than volume | All training outputs should use consistent hedging format, [DRAFT] tag, ≤120 words |
| Hand-authored examples outperform synthetic augmentation | The 5 hand-authored adversarial tasks in train.jsonl are disproportionately valuable |

**Recommended action:** Treat the 5 hand-authored adversarial tasks as high-priority training examples (oversample 3× relative to programmatic tasks). Their edge-case coverage exceeds what programmatic generation produces for the same signal conditions.
