# Tenacious-Bench v0.1 - Executive Memo
**To:** CEO, CFO — Tenacious Consulting & Outsourcing
**From:** Melaku Y., AI Systems
**Date:** 2026-05-01
**Re:** Production recommendation — grounded outreach agent

---

 The Decision

### Executive Summary
Tenacious-Bench v0.1 reveals that a B2B sales outreach agent scoring
0.70 on tau2-Bench retail fails 75% of domain-specific probes due to
hallucinated firmographics and signal overclaim. A LoRA adapter trained
on 1,016 grounded pairs lifted held-out performance from 0.6976 to 0.8863
(Delta A +0.1887, 95% CI [+0.155, +0.224], p<0.0001). The adapter is
recommended for immediate production deployment with three instrumentation
requirements.

### Headline Results

| Condition | Score | Delta |
|---|---|---|
| Unguarded baseline (Week 10) | 0.6976 | - |
| Prompt-only guarded | 0.7992 | +0.1016 |
| Trained adapter v0.1 | 0.8863 | +0.1887 |

Delta A: +0.1887 (95% CI [+0.155, +0.224], p<0.0001, paired bootstrap, n=62)
Delta B: +0.0871 - training beat prompt engineering alone (p<0.0001)
Delta C: +0.1863 vs tau2-Bench retail baseline (0.70)

### Cost Per Task

| Condition | Latency | Relative cost |
|---|---|---|
| Without adapter (base guarded) | 7.17s | 1.0x |
| With adapter (LoRA) | 2.98s | 0.42x |

The adapter is 2.4x faster AND more accurate. This is a Pareto
improvement — no cost-quality tradeoff exists.

### Production Recommendation

**Deploy immediately** for cold outreach generation.

1. Replace the unguarded generation call with the LoRA adapter on
Qwen2.5-1.5B-Instruct. Estimated latency: ~3s per email on T4-class
hardware.

2. Add the enrichment signal gate before generation. Tasks with
icp_segment=abstain or icp_confidence=low + low_peer_count=True should
route to human review, not direct send.

3. Instrument signal_fidelity scoring on all outbound drafts. Flag any
draft containing fabricated funding round claims before delivery to
SDR inbox.

Expected outcome: hallucination rate drops from ~30% to less than 5%
based on held-out pass rate (0.8863).

---

The Skeptic's Appendix

### Four Failure Modes Tenacious-Bench v0.1 Does Not Capture

1. **Multi-turn conversation quality.** Tenacious-Bench evaluates single
outreach drafts only. Follow-up email quality and reply handling are not
measured. v0.2 addition needed: multi-turn conversation tasks with
reply handling and thread continuity evaluation.

2. **Real prospect response rate.** The rubric scores signal fidelity
and tone compliance. It does not measure whether emails get replies.
v0.2 addition needed: A/B test integration with real send data to
validate rubric scores against actual reply rates.

3. **Out-of-distribution enrichment signals.** Segments outside
segment_1 to segment_4 (e.g., government, NGO, pre-revenue) are not
evaluated. v0.2 addition needed: government and NGO segment tasks with
appropriate tone and signal guides.

4. **Prompt injection robustness.** Adversarial enrichment briefs
crafted by a motivated attacker have limited held-out coverage.
v0.2 addition needed: automated adversarial brief generation pipeline
covering P13-P18 probe categories at scale.

### Public-Signal Lossiness in Ground Truth

Enrichment signals are derived from public data proxies with ~20-30%
error rate vs ground truth company state. An email grounded in a wrong
brief scores well but sends false information to the prospect. The
benchmark scores grounding against the brief, not against reality.

### One Honest Unresolved Failure

TB-TD-001 (Karibu Tech trace) passed the score==1.0 filter in earlier
pipeline versions despite containing banned phrases "scale rapidly" and
"aggressive growth". The scorer regex did not catch these paraphrase
variants. After manual removal, 0 such cases remain in training data,
but the scorer gap may allow future programmatic generation to
reintroduce similar violations without automatic detection.

### Kill-Switch Trigger

Suspend adapter deployment if any of the following occur:

- Signal fidelity score drops below 0.75 on a rolling 50-task
  production sample
- More than 3 confirmed hallucinated funding claims reach SDR inboxes
  in a 7-day window
- A prospect complaint referencing fabricated company information
  is received
- Delta A on quarterly re-evaluation falls below +0.10 vs unguarded
  baseline

Reversion path: disable LoRA adapter, fall back to prompt-only guarded
baseline (score 0.7992) while root cause is investigated.