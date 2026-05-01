# Tenacious-Bench LoRA Adapter v0.1

## Model Details
- **Base model:** Qwen2.5-1.5B-Instruct
- **Adapter type:** LoRA (rank 16, alpha 32)
- **Training data:** Tenacious-Bench v0.1 train partition (1,016 examples, score ≥ 0.75)
- **Training steps:** 100
- **Final loss:** 0.1148

## Intended Use
B2B sales outreach email generation grounded in enrichment signals.
Reduces signal overclaim (FC-3) and hallucinated firmographics (FC-1).

## Evaluation Results
| Metric | Value |
|---|---|
| Baseline (unguarded) | 0.6976 |
| Base guarded (prompt-only) | 0.7992 |
| Adapter | 0.8863 |
| Delta A | +0.1887 (p<0.0001) |
| Delta B | +0.0871 (p<0.0001) |
| Delta C vs τ²-Bench | +0.1863 |
| Latency vs base | 2.4× faster |

## Limitations
- Trained on synthetic and programmatic data
- Domain-specific to B2B SaaS outreach
- Score filter ≥ 0.75 may include some borderline examples