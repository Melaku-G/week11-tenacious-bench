# Tenacious-Bench v0.1

A domain-specific evaluation benchmark for B2B sales outreach agents. Designed to catch
failure modes that general benchmarks (tau2-Bench retail, HELM, MTEB) cannot detect in
the Tenacious Consulting & Outsourcing conversion engine.

---

## Why This Benchmark Exists

tau2-Bench retail grades binary task resolution against a policy document. For Tenacious
outreach agents it misses six critical dimensions — see [`audit_memo.md`](audit_memo.md)
for the full gap analysis. The short version:

| tau2-Bench gap | Failure mode this bench catches |
|----------------|--------------------------------|
| No signal grounding check | FC-3: overclaims on low hiring signal (~40% unguarded) |
| No tone guide grading | Banned phrases, upbeat copy on layoff signals (~35%) |
| No segment gate | FC-2: AI pitch to ai_maturity_score < 2 company (~20%) |
| No confidence hedging | FC-5: missing hedging when icp_confidence=low (~25%) |
| No role-conditioned grading | Contact-role mismatch (HR vs CTO, competitor vs buyer) |
| No enrichment pipeline | FC-4: prompt injection via company_name field (~60%) |

---

## Dataset

| Partition | File | Tasks | Mean score | Pass rate | Use |
|-----------|------|-------|------------|-----------|-----|
| Train | `tenacious_bench_v0.1/train.jsonl` | 217 (56%) | 0.783 | 61.3% | SFT training data |
| Dev | `tenacious_bench_v0.1/dev.jsonl` | 105 (27%) | 0.747 | 53.3% | Iteration during authoring |
| Held-out | `tenacious_bench_v0.1/held_out.jsonl` | 62 (16%) | 0.732 | 53.2% | Sealed — final ablation only |

_Updated 2026-04-29 post-IRA: signal_fidelity patterns extended (IRA R1 vs R3 κ=0.77, PASS)._

**Total: 384 tasks** across four authoring modes:

| Mode | Count | Script |
|------|-------|--------|
| Programmatic | 300 | `generation_scripts/programmatic.py` |
| Multi-LLM synthesis | 74 | `generation_scripts/synthesis.py` |
| Trace-derived | 5 | `generation_scripts/_add_trace_and_adversarial.py` |
| Hand-authored adversarial | 5 | `generation_scripts/_add_trace_and_adversarial.py` |

---

## Rubric

Every task is scored on five machine-verifiable dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| `signal_fidelity` | 0.30 | No unsupported growth/funding claims |
| `tone_compliance` | 0.20 | Zero banned phrases |
| `segment_gate` | 0.20 | Seg 4 AI pitch only when `ai_maturity_score >= 2` |
| `confidence_hedging` | 0.15 | Hedging present when `icp_confidence=low` or `low_peer_count=True` |
| `format_compliance` | 0.15 | `[DRAFT]` tag present, body ≤ 120 words, no bench capacity commitment |

**Pass threshold: 0.75** (weighted sum across applicable dimensions)

Each dimension returns 0 or 1 — no partial credit. See [`schema.json`](schema.json) for
the full field specification and three worked examples.

---

## Quick Start

### 1. Generate tasks

```bash
# Programmatic (no API needed — good first step)
python bench/generation_scripts/programmatic.py \
    --partition train --count 90 --seed 42

python bench/generation_scripts/programmatic.py \
    --partition dev --count 45 --seed 43

# Trace-derived (requires eval/trace_log.jsonl or probes/held_out_traces.jsonl)
python bench/generation_scripts/trace_derived.py \
    --trace-log probes/held_out_traces.jsonl \
    --partition train --limit 60

# Multi-LLM synthesis (requires OPENROUTER_API_KEY)
export OPENROUTER_API_KEY=sk-or-v1-...
python bench/generation_scripts/synthesis.py \
    --partition dev --count 50
```

### 2. Score a partition

```bash
python bench/scoring_evaluator.py \
    bench/tenacious_bench_v0.1/dev.jsonl \
    --output bench/tenacious_bench_v0.1/dev.jsonl
```

Scores are written in-place (the `score` and `dimension_scores` fields are populated).
Tasks with `score >= 0.75` pass. All three partitions are pre-scored in the repo.

### 3. Train LoRA adapter (Colab T4)

```bash
# Requires unsloth — install on Colab
python bench/training/train.py \
    --train-file bench/tenacious_bench_v0.1/train.jsonl \
    --output-dir bench/training/checkpoints \
    --max-steps 300
```

---

## Directory Reference

```
bench/
├── README.md                        ← this file
├── schema.json                      ← task schema + 3 worked examples
├── scoring_evaluator.py             ← machine-verifiable scorer (CLI)
├── audit_memo.md                    ← tau2-Bench gap analysis (6 dimensions)
├── methodology.md                   ← Path A declaration + contamination protocol
├── datasheet.md                     ← Gebru et al. 7-section datasheet
├── model_card.md                    ← Mitchell et al. model card
├── inter_rater_agreement.md         ← IRA protocol (κ target ≥ 0.75)
├── contamination_check.json         ← 5-check contamination results (pending)
├── evidence_graph.json              ← failure mode → probe ID → trace ID links
├── generation_scripts/
│   ├── trace_derived.py             ← convert probes/held_out_traces.jsonl → tasks
│   ├── programmatic.py              ← parameter sweep + failure injection
│   └── synthesis.py                 ← OpenRouter LLM generate + judge filter
├── training/
│   └── train.py                     ← Unsloth LoRA SFT (Qwen 2.5 1.5B, rank 16)
├── ablations/
│   └── ablation_results.json        ← 3-variant comparison (pending)
└── tenacious_bench_v0.1/            ← generated dataset (gitignored: held_out.jsonl)
    ├── train.jsonl
    ├── dev.jsonl
    └── held_out.jsonl               ← SEALED — do not use for training
```

---

## Reproducibility

| Component | Value |
|-----------|-------|
| Programmatic seed | `--seed 42` (train), `--seed 43` (dev) |
| Synthesis seed | `--seed 99` |
| Generation model | `deepseek/deepseek-chat` |
| Judge model | `meta-llama/llama-3.1-8b-instruct` (different family from DeepSeek — Li et al. 2025) |
| LoRA base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| LoRA rank / alpha | 16 / 32 |
| Training steps | 300 |

---

## Key Design Decisions

**Why Path A (SFT) over Path B (judge) or Path C (PRM)?**  
FC-3 and FC-1 are generation-quality failures — the model defaults to optimistic SDR copy
from its training distribution regardless of signal input. SFT on grounded (input, output)
pairs retrains the behavior directly. See [`methodology.md`](methodology.md) for the full
argument and contingency plan.

**Why not use tau2-Bench held-out as a proxy?**  
tau2-Bench pass@1 (0.70) does not predict Tenacious failure rates — unguarded baseline is
~75% failure, guarded is ~30% residual. The two evaluations measure orthogonal properties.

**Held-out partition is sealed.**  
Do not use `held_out.jsonl` for training data selection, hyperparameter tuning, or interim
reporting. It is used exactly once — for the final ablation on Day 6.


# Tenacious-Bench v0.1

A domain-specific evaluation benchmark for B2B sales outreach agents.

## What This Is

Tenacious-Bench v0.1 is a 408-task benchmark covering failure modes that 
general benchmarks (τ²-Bench, HELM) do not capture for B2B SDR agents:

- **FC-1** Hallucinated firmographics (~30% unguarded rate)
- **FC-2** Segment-gate bypass — AI pitch to low-maturity companies (~20%)
- **FC-3** Signal overclaim — fabricated funding/growth claims (~40%)
- **FC-5** Missing confidence hedging (~25%)

## Results

| Condition | Score | Delta |
|---|---|---|
| Unguarded baseline | 0.6976 | — |
| Prompt-only guarded | 0.7992 | +0.1016 |
| **Trained adapter (v0.1)** | **0.8863** | **+0.1887** |

Delta A: +0.1887 (95% CI [+0.155, +0.224], p<0.0001, n=62)  
Delta B: +0.0871 — training beat prompt-only (p<0.0001)  
Adapter is 2.4x faster than base guarded model.

## Dataset

- HuggingFace: https://huggingface.co/datasets/Mella123/tenacious-bench-v0.1
- 408 tasks: 235 train / 111 dev / 62 held-out
- Sources: programmatic, synthesis, trace-derived, hand-authored

## Quickstart

```python
from datasets import load_dataset

dataset = load_dataset("Mella123/tenacious-bench-v0.1", split="train")
print(dataset[0])
```

## Adapter

- HuggingFace: https://huggingface.co/Mella123/tenacious-bench-lora
- Base: Qwen2.5-1.5B-Instruct
- LoRA rank 16, alpha 32, trained on 1,016 examples

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
model = PeftModel.from_pretrained(base, "Mella123/tenacious-bench-lora")
tokenizer = AutoTokenizer.from_pretrained("Mella123/tenacious-bench-lora")
```

## Repo Structure
tenacious_bench_v0.1/   — dataset partitions
training_data/          — SFT training file
adapter/                — LoRA weights + loss curve
synthesis_memos/        — 7 literature review memos
ablation_results.json   — Delta A/B/C + Cost-Pareto
evidence_graph.json     — claims linked to sources
memo.pdf                — CEO/CFO executive memo
training_run.log        — hyperparameters + loss curve

 Community

- τ²-Bench issue: https://github.com/sierra-research/tau2-bench/issues/280

## Citation

```bibtex
@misc{tenacious-bench-2026,
  title={Tenacious-Bench v0.1: Domain-Specific Evaluation for B2B Sales Outreach Agents},
  author={Melaku Y.},
  year={2026},
  url={https://huggingface.co/datasets/Mella123/tenacious-bench-v0.1}
}
```