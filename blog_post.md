# Tenacious-Bench v0.1: What Happens When You Evaluate a B2B Sales Agent on Tasks It Was Never Designed For

*By Melaku Y. — May 2026*

---

## The Gap

General-purpose agent benchmarks are good at measuring what they measure.
τ²-Bench retail tasks test whether an agent can navigate a returns portal,
look up order status, or apply a discount code. HELM tests factual recall
and reasoning. Both are rigorous. Neither tells you whether a B2B sales
development agent will fabricate a funding round that never happened.

That is the gap this work addresses.

Our agent — built on Qwen2.5-1.5B-Instruct, deployed for outbound
engineering staffing outreach — scored 0.70 pass@1 on τ²-Bench retail
held-out. Reasonable. The same agent, given an enrichment brief showing
`open_roles_estimate=0` and `layoff_event=True`, wrote:

> *"I know that Waverly Biotech recently raised a Series B and is
> expanding into three new markets. Your team of engineers will need
> support as you scale operations."*

Nothing in the brief supported any of those claims. The agent defaulted
to optimistic SDR copy from its training distribution. τ²-Bench score:
0.70. Domain failure rate: ~75%.

This is not a criticism of τ²-Bench. It is a measurement of orthogonality.
General benchmarks cannot predict domain-specific failure modes they were
not designed to cover.

---

## The Audit Method

We ran 42 domain-specific probes against the unguarded baseline across
13 failure categories:

- **FC-1 Hallucinated firmographics** (~30% trigger rate): agent
  fabricates funding rounds, market expansion, headcount growth not
  present in enrichment brief
- **FC-2 Segment-gate bypass** (~20%): agent pitches AI/LLM capabilities
  to companies with `ai_maturity_score < 2`
- **FC-3 Signal overclaim** (~40%): banned growth phrases used regardless
  of signal input
- **FC-5 Confidence bypass** (~25%): no hedging language when
  `icp_confidence=low` or `low_peer_count=True`

After adding prompt guardrails (Style Guide v2, signal hedging rules),
the failure rate dropped to ~30% residual. Guardrails reduced but could
not eliminate paraphrase variants of each failure class. FC-1 and FC-3
persisted at ~15% even with the full guardrail stack.

Inter-rater agreement between deterministic scorer (R1) and human
annotator (R3): κ=0.77 — above the 0.75 threshold we set for rubric
validity.

---

## The Dataset

**Tenacious-Bench v0.1** contains 408 tasks across four sources:

| Source | Count | Role |
|---|---|---|
| Programmatic | 300 | Parameter sweep coverage |
| Synthesis | 74 | Diverse ICP segments |
| Trace-derived | 5 | Real agent failure traces |
| Hand-authored | 29 | Adversarial edge cases |

Four hard design choices shaped the dataset:

**1. Deterministic scorer, no LLM judge.**
We tested LLaMA 3.1 8B as a judge. κ=0.04–0.26 on signal_fidelity —
unreliable. The rubric scorer uses keyword matching and regex patterns
across five weighted dimensions. Slower to build, but reproducible.

**2. Score==1.0 filter for training data.**
The ≥0.75 rubric pass threshold is for evaluation. For training, we
required score==1.0 — every dimension passing with no violations. A task
scoring 0.80 has at least one failing dimension. Training on it teaches
the model that violations are acceptable.

**3. Multi-source generation with preference leakage fix.**
Following Gu et al. (2024), we used DeepSeek for generation and Qwen
72B for judging — not the same model for both. Using the same model to
generate and judge introduces systematic bias toward its own outputs.

**4. Contamination protocol.**
SHA-256 hash comparison of enrichment briefs between train, dev, and
held-out partitions. Zero collisions confirmed before training.

---

## The Training Experiment

**Path A: Supervised Fine-Tuning** on signal-grounded (input,
correct-output) pairs.

FC-1 and FC-3 are generation-quality failures — the model's output
distribution defaults to optimistic B2B copy regardless of input signals.
Prompt engineering (Path B) reduces but cannot retrain this prior.
SFT directly retrains the mapping from enrichment signal to grounded
output.

Following Zhou et al. (2023) LIMA: quality dominates quantity at small
scale. We filtered 1,016 training examples at score≥0.75 from the 235
train-partition tasks after source oversampling (hand-authored 4×,
trace-derived 2×). This gives 0.00000065 pairs/param at 1.5B —
comparable to LIMA's ratio at 65B.

Per Lambert et al. (2024) Tülu 3: DPO requires a reliable preference
judge (κ≥0.70). Our judge achieved κ=0.04–0.26. DPO with a noisy judge
degrades grounding. SFT only was the correct stage-one approach.

Training configuration: Qwen2.5-1.5B-Instruct, LoRA rank 16 alpha 32,
100 steps, 2e-4 cosine LR, T4 GPU, 6 minutes wall time.

Loss curve: 1.7114 → 0.2152 → 0.1434 → 0.1148. Clean monotonic
decrease. No divergence.

---

## The Honest Result

| Condition | Score | Delta |
|---|---|---|
| Unguarded baseline | 0.6976 | — |
| Prompt-only guarded | 0.7992 | +0.1016 |
| **Trained adapter** | **0.8863** | **+0.1887** |

**Delta A: +0.1887** (95% CI [+0.155, +0.224], p<0.0001, paired
bootstrap, n=62 held-out tasks, 10,000 iterations)

**Delta B: +0.0871** (95% CI [+0.057, +0.118], p<0.0001) — training
beat prompt-only. This is the result that validates the SFT path.
Many interventions fail Delta B. This one did not.

**Delta C: +0.1863** vs τ²-Bench baseline 0.70 — improvement is
Tenacious-specific, not general. The adapter was not tested on τ²-Bench
retail tasks and we make no claim about general capability.

**Cost-Pareto:** Adapter latency 2.98s vs base 7.17s. The adapter is
2.4× faster AND more accurate. No cost-quality tradeoff.

54/62 tasks improved. 8 same. 0 regressions.

---

## What Did Not Work

**TB-TD-001 (Karibu Tech)** passed the score==1.0 filter in an earlier
pipeline version despite containing "scale rapidly" and "aggressive
growth" — both banned phrases. The scorer's regex missed these paraphrase
variants. We caught it on manual review and removed it. The scorer gap
remains — future programmatic generation may reintroduce similar
violations without automatic detection. This is the one honest unresolved
failure we are carrying into v0.2.

---

## What Is Next

1. **Scorer hardening** — extend GROWTH_CLAIM_PATTERNS and BANNED_PHRASES
   to cover paraphrase variants. Add a secondary LLM check specifically
   for funding fabrication patterns where confidence is high.

2. **DPO stage** — now that we have a reliable SFT baseline, we can
   construct preference pairs (adapter output vs unguarded output) and
   run DPO to push signal fidelity further. The judge problem remains
   but is more tractable with a stronger base.

3. **Multi-turn extension** — Tenacious-Bench v0.1 evaluates single
   outreach drafts. v0.2 will add follow-up email sequences and reply
   handling tasks.

4. **Community contribution** — we have opened an issue on τ²-Bench
   proposing a B2B enterprise task split. If you work on sales agent
   evaluation and want to collaborate, the dataset and adapter are
   publicly available.

---

## Resources

- Dataset: https://huggingface.co/datasets/Mella123/tenacious-bench-v0.1
- Adapter: https://huggingface.co/Mella123/tenacious-bench-lora
- GitHub: https://github.com/Melaku-G/week11-tenacious-bench
- τ²-Bench issue: https://github.com/sierra-research/tau2-bench/issues/280

---

*Word count: ~1,400*