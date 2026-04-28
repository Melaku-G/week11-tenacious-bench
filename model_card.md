# Model Card — Tenacious-Bench SFT v0.1

_Following Mitchell et al. (2019) Model Cards for Model Reporting._

---

## Model Details

| Field | Value |
|-------|-------|
| Base model | Qwen/Qwen2.5-1.5B-Instruct (or 2B if T4 memory allows) |
| Fine-tuning method | LoRA (rank=16, alpha=32, dropout=0.05) |
| Training framework | Unsloth + TRL SFTTrainer |
| Target hardware | Colab T4 (16GB VRAM) |
| Training data | `bench/tenacious_bench_v0.1/train.jsonl` (positive pairs, score ≥ 0.8) |
| Training steps | Target 300 (adjustable) |
| Adapter checkpoint | `bench/training/checkpoints/lora_adapter/` |
| Status | ⏳ Pending training run |

---

## Intended Use

**Primary use:** Generate grounded, guardrail-compliant B2B outreach email drafts for
Tenacious Consulting & Outsourcing. The model is fine-tuned to produce hedged,
evidence-anchored copy when enrichment signals are low — without requiring an explicit
system prompt with guardrail rules.

**Intended users:** Internal Tenacious SDR pipeline; evaluation via Tenacious-Bench v0.1.

**Out-of-scope uses:**
- General-purpose email generation
- Domains outside B2B tech staffing/consulting
- Any outreach without enrichment signal brief

---

## Training Data

Positive pairs drawn from `train.jsonl` where `score >= 0.8` on the Tenacious-Bench rubric.
See [datasheet.md](datasheet.md) for full dataset documentation.

Dataset composition at training time:
- Trace-derived: ~30%
- Programmatic: ~30%
- Multi-LLM synthesis (judge-filtered): ~25%
- Hand-authored adversarial: ~15%

---

## Evaluation

Evaluated on the **held-out partition only** (`bench/tenacious_bench_v0.1/held_out.jsonl`).
Held-out partition is sealed — not used for training or hyperparameter selection.

| Metric | Baseline (unguarded) | Baseline (guarded) | SFT v0.1 |
|--------|---------------------|--------------------|----------|
| Held-out mean score | TODO | TODO | TODO |
| signal_fidelity | TODO | TODO | TODO |
| tone_compliance | TODO | TODO | TODO |
| segment_gate | TODO | TODO | TODO |
| confidence_hedging | TODO | TODO | TODO |
| format_compliance | TODO | TODO | TODO |

See [ablations/ablation_results.json](ablations/ablation_results.json) for full results.

---

## Limitations

1. **Synthetic training data**: All candidate outputs in the training set are either
   agent-generated traces, programmatic injections, or LLM synthesis. Real human-written
   positive examples would likely improve tone compliance.

2. **Small model size**: 1.5–2B parameter model may not generalise to edge cases outside
   the probe parameter space.

3. **Single-turn evaluation**: The model is evaluated on single email drafts; it has not
   been tested on multi-turn conversation quality.

4. **Hallucination floor**: FC-1 hallucination is the hardest failure mode to fix with SFT
   alone — the model needs to learn "don't make up" rather than "make up the right thing."

---

## Ethical Considerations

- No PII in training data (company names synthetic or public Crunchbase data)
- Model outputs are drafts only (`[DRAFT]` tag enforced) — human review required before send
- Not intended for mass unsolicited outreach; designed for signal-qualified prospects only
