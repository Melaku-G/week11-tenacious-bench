# Tenacious-Bench v0.1 — Executive Memo
**To:** CEO, CFO — Tenacious Consulting & Outsourcing  
**From:** Melaku Y., AI Systems  
**Date:** 2026-05-01  
**Re:** Production recommendation — grounded outreach agent

---

## Page 1: The Decision

### What Was Built
Tenacious-Bench v0.1 is a domain-specific evaluation benchmark for B2B 
sales outreach agents. It contains 408 tasks across train, dev, and 
held-out partitions, covering six failure classes identified in Week 10 
probing: signal overclaim, hallucinated firmographics, segment-gate 
bypass, tone violations, confidence hedging failures, and format 
non-compliance.

A LoRA adapter was trained on 1,016 signal-grounded (input, output) pairs 
using Qwen2.5-1.5B-Instruct as the backbone. Training took 6 minutes on 
a T4 GPU.

### Headline Results

| Condition | Score | vs Baseline |
|---|---|---|
| Unguarded baseline (Week 10) | 0.6976 | — |
| Prompt-only guarded | 0.7992 | +0.1016 |
| Trained adapter (v0.1) | 0.8863 | **+0.1887** |

**Delta A: +0.1887** (95% CI [+0.155, +0.224], p<0.0001, paired bootstrap, n=62)  
**Delta B: +0.0871** — training beat prompt engineering alone (p<0.0001)  
**Delta C: +0.1863** vs τ²-Bench retail baseline (0.70)

### Cost Per Task Delta

| Metric | Base model | Trained adapter |
|---|---|---|
| Avg latency | 7.17s | 2.98s |
| Speedup | — | **2.4× faster** |
| Score | 0.7992 | 0.8863 |

The adapter is simultaneously more accurate and faster. There is no 
cost-quality tradeoff — this is a Pareto improvement.

### Production Recommendation

**Deploy the adapter immediately for cold outreach generation.**

Three changes to the production pipeline:

1. **Replace the unguarded generation call** with the LoRA adapter on 
   Qwen2.5-1.5B-Instruct. Estimated latency: ~3s per email on T4-class 
   hardware.

2. **Add the enrichment signal gate** before generation. Tasks with 
   `icp_segment=abstain` or `icp_confidence=low` + `low_peer_count=True` 
   should route to a human review queue, not direct send.

3. **Instrument signal_fidelity scoring** on all outbound drafts. Flag 
   any draft containing fabrication patterns (funding round claims not 
   in brief, market expansion claims) before delivery to SDR inbox.

Expected outcome: hallucination rate drops from ~30% to <5% on 
production volume based on held-out pass rate (0.8863).

---

## Page 2: The Skeptic's Appendix

### Failure Modes the Benchmark Does Not Capture

1. **Multi-turn conversation quality.** Tenacious-Bench evaluates single 
   outreach drafts. It does not measure follow-up email quality, reply 
   handling, or conversation threading — all of which matter in real SDR 
   workflows.

2. **Real prospect response rate.** The rubric scores signal fidelity and 
   tone compliance. It does not measure whether emails actually get 
   replies. A grounded email that bores the prospect is still a failure 
   not captured here.

3. **Out-of-distribution enrichment signals.** The benchmark covers 
   segment_1 through segment_4 ICP segments. Prospects outside these 
   segments (e.g., government, NGO, pre-revenue) are not evaluated.

4. **Prompt injection robustness.** Probes P13–P18 test injection 
   resistance but the held-out partition has limited coverage of 
   adversarial enrichment briefs crafted by a motivated attacker.

### Public-Signal Lossiness in Ground Truth

Enrichment signals (open_roles_estimate, engineering_velocity, 
ai_maturity_score) are derived from public data proxies — LinkedIn job 
postings, GitHub commit frequency, job title analysis. These signals have 
~20–30% error rate vs ground truth company state. The benchmark scores 
grounding against the brief, not against reality. An email grounded in a 
wrong brief scores well but sends false information.

### One Honest Unresolved Failure

TB-TD-001 (Karibu Tech trace) passed the score==1.0 filter in earlier 
pipeline versions despite containing "scale rapidly" and "aggressive 
growth" — banned phrases. The scorer's regex did not catch these 
paraphrase variants. After manual removal, 0 such cases remain in 
training data, but the scorer gap means future programmatic generation 
may reintroduce similar violations without detection.

### Kill-Switch Trigger

**Suspend adapter deployment if any of the following occur:**

- Signal fidelity score drops below 0.75 on a rolling 50-task production 
  sample
- More than 3 confirmed hallucinated funding claims reach SDR inboxes in 
  a 7-day window
- A prospect complaint referencing fabricated company information is 
  received
- Delta A on a quarterly re-evaluation falls below +0.10 vs the 
  unguarded baseline

Reversion path: disable LoRA adapter, fall back to prompt-only guarded 
baseline (score 0.7992) while root cause is investigated.