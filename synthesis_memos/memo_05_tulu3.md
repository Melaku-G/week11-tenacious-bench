# Memo 05 — Tülu 3: Pushing Frontiers in Open Language Model Post-Training

**Citation:** Lambert et al. (2024). *Tülu 3: Pushing Frontiers in Open Language Model Post-Training.* Allen Institute for AI.

**Path relevance:** Path A — Supervised Fine-Tuning of a Generation Component

---

## Core Claim

Tülu 3 demonstrates that a structured, staged post-training pipeline — SFT on diverse high-quality instruction data, followed by preference tuning (DPO) and optional RLVR — achieves frontier-parity on open models. The key finding for SFT practitioners: **data composition trumps raw volume**. A carefully selected 939K-task mixture (deduped from >2M candidates) consistently outperforms models trained on larger noisy sets.

---

## Methods Summary

1. **Data curation** — Multi-source mixture: FLAN, ShareGPT, WizardLM, open-instruct annotated, synthetic math/code. Applied deduplication (MinHash), quality filtering (perplexity + length distribution), and domain rebalancing.
2. **SFT stage** — Standard next-token prediction on (prompt, response) pairs. Base: Llama 3.1 8B/70B. 3 epochs, cosine LR decay.
3. **Preference tuning (DPO)** — Preference pairs generated via LLM judge from SFT outputs. Applied after SFT to fix failure modes not addressed by imitation alone.
4. **RLVR (optional)** — Reinforcement learning with verifiable rewards (math, code). Improves structured-output tasks.
5. **Evaluation** — MMLU, HumanEval, GSM8K, AlpacaEval, custom chat benchmarks. Tülu 3 70B matches or beats GPT-4 Turbo on most axes.

---

## Why This Supports Path A for Tenacious-Bench

FC-3 (over-claim on hiring signals) and FC-1 (hallucinated firmographics) are generation failures — the model produces optimistic SDR copy regardless of enrichment signal. Tülu 3's central finding is that **SFT on grounded (prompt, correct-output) pairs fixes distributional bias** before preference tuning is applied. The analogy is direct: Tenacious train pairs where the model correctly hedges (`open_roles=0, velocity=low → conditional language`) are the same mechanism — grounded imitation of the desired generation behaviour.

Lambert et al. show that for domain-specific failures, even a small SFT mixture (≈1K targeted pairs) can shift behaviour. The 217-task Tenacious train partition aligns with this — small, high-quality, domain-targeted.

---

## One Disagreement

Tülu 3 advocates a DPO preference-tuning stage after SFT to further reduce failure rates. For Tenacious-Bench, this would require paired (good-output, bad-output) examples with an ICP-capable judge. The current evidence does not support this: our judge evaluation (memo_04_gu_llm_judge.md) showed LLaMA 8B achieves κ=0.04–0.26 overall, making automated preference pair generation unreliable.

**Disagreement:** Preference tuning should not be added at this stage. The Tenacious judge quality is insufficient to generate trustworthy preference pairs — DPO on noisy labels risks degrading the signal-fidelity gains from SFT. Hold preference tuning for v0.2 when a Claude Sonnet-class judge is available (IRA target: κ≥0.75 on all dimensions).

---

## Implications for Tenacious-Bench Training

| Tülu 3 Finding | Tenacious-Bench Application |
|----------------|---------------------------|
| Data composition > volume | Use train.jsonl tasks with score≥0.80 only (IRA-validated quality floor) |
| Staged pipeline: SFT first | SFT on grounded pairs; do not jump to DPO without a capable judge |
| Domain-specific SFT shifts distributional bias | FC-3/FC-1 failures are distributional — SFT is the right lever |
| MinHash dedup improves signal | `scoring_evaluator.py` filters already eliminate low-quality tasks |

**Recommended action:** Filter train.jsonl to tasks with `score >= 0.80` before SFT (reduces training set to ~61% high-confidence pairs, removes noise from borderline-pass tasks).
