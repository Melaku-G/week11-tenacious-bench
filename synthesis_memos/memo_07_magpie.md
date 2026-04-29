# Memo 07 — Magpie: Alignment Data Synthesis from Scratch by Prompting Aligned LLMs

**Citation:** Xu et al. (2024). *Magpie: Alignment Data Synthesis from Scratch by Prompting Aligned LLMs.* arXiv:2406.08464.

**Path relevance:** Path A — Supervised Fine-Tuning of a Generation Component

---

## Core Claim

Magpie shows that **aligned LLMs can self-generate high-quality instruction-response pairs** by exploiting the autoregressive system prompt gap: given only a user-turn template (no instruction), an aligned LLM will auto-complete a plausible instruction + a high-quality response. This produces large-scale training data without human curation, seed tasks, or backtranslation. Magpie-generated 300K pairs match or exceed WizardLM and ShareGPT on MMLU, MT-Bench, and AlpacaEval.

---

## Methods Summary

1. **Prompt structure** — Feed the LLM the system prompt + user-turn tag only (no content). The model generates a realistic instruction in the user role.
2. **Quality filtering** — LLM-as-judge (Qwen 72B, cross-family) scores each (instruction, response) pair on `instruction_difficulty`, `response_quality`, `instruction_coherence`. Pairs below threshold discarded.
3. **Scale** — Generates 300K–1M pairs from Llama 3 and Qwen 2.5. Filtering reduces to ~200K high-quality pairs.
4. **Training** — Standard SFT on LLaMA 3 8B/70B. Matches Tülu 3 on most evaluations.
5. **Key observation** — The self-generated instruction distribution mirrors the system-prompt space the model was aligned on, avoiding distribution shift.

---

## Why This Supports Path A for Tenacious-Bench

The synthesis.py pipeline already implements Magpie's core idea: prompt an LLM with the Tenacious system context and let it generate (brief, email) pairs, then filter with a cross-family judge. The 74 synthesis tasks in the benchmark were generated this way. Magpie validates the approach: self-generated data from a model trained on similar distributions is higher quality than random instruction templates.

For FC-3 and FC-1, Magpie-style generation with explicit failure-injection prompts can extend the training set cheaply. The `synthesis.py` pipeline (DeepSeek generate + LLaMA judge) uses the same cross-family judge rotation that Magpie recommends to prevent preference leakage.

---

## One Disagreement

Magpie relies on scale — 300K+ pairs — and a large LLM (Llama 3 70B) as the generator to produce sufficient diversity and difficulty coverage. For Tenacious-Bench, the synthesis pipeline uses `deepseek/deepseek-chat` (a smaller, instruction-tuned model) and generates only 74 tasks. Xu et al. show that smaller generator models produce lower-difficulty instructions that cluster around easy, common patterns.

**Disagreement:** Magpie's scale and generator-quality requirements are not met by the current Tenacious synthesis pipeline. The 74 synthesis tasks likely under-represent hard failure modes (adversarial paraphrases, edge-case signal combinations) because DeepSeek defaults to canonical examples rather than stress-testing the rubric. The IRA supports this: the R2 judge (which flags over-optimism more aggressively than R1) detected 5 tasks in the synthesis subset where R1 passed but growth language was arguably unsupported. Magpie-at-scale would need a 70B+ generator — beyond the current compute budget. The implication for Day 5 training: weight synthesis tasks *lower* (not higher) than programmatic + hand-authored, since their difficulty distribution is compressed.

---

## Implications for Tenacious-Bench Training

| Magpie Finding | Tenacious-Bench Application |
|----------------|---------------------------|
| Self-generation mirrors system-prompt distribution | synthesis.py tasks are high-distribution-fidelity (Tenacious context baked in) |
| Cross-family judge required for quality filtering | DeepSeek generate + LLaMA judge rotation is correct per this finding |
| Scale matters for difficulty diversity | 74 synthesis tasks are insufficient for hard-adversarial coverage — supplement with programmatic injection |
| Smaller generators compress difficulty distribution | Treat synthesis tasks as easy-to-medium difficulty; rely on hand-authored for hard cases |

**Recommended action for train.py:** Assign sampling weights: hand_authored=4×, programmatic=1×, synthesis=0.75×, trace_derived=2×. This reflects difficulty distribution from the IRA and Magpie's generator-quality finding. Do not upsample synthesis tasks to compensate for small count — their difficulty ceiling is lower than programmatic.
