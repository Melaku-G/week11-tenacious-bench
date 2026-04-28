# Synthesis Memo 01 — Synthetic Data for Language Models

**Paper:**
- Liu et al. (2024). *Best Practices and Lessons Learned on Synthetic Data for Language Models.*
  COLM 2024.

**Written by:** Tenacious-Bench authoring team
**Date:** 2026-04-28
**Relevance to project:** Direct foundation for the four-mode dataset construction strategy
and the judge-filter-before-write architecture in Tenacious-Bench v0.1.

---

## Core Argument

Liu et al. argue that synthetic data is now a practical substitute for human-annotated data
in both training and evaluation, but only when three quality conditions hold:
*factuality* (no false claims introduced), *fidelity* (reflects real distribution patterns),
and *unbiasedness* (does not amplify distribution skew). The paper surveys evidence across
reasoning, alignment, safety, and multimodal domains, finding consistent gains when
synthetic data is carefully controlled and filtered, and consistent failures when it is not.
The operational recommendation: generate at volume, filter aggressively, write only what
passes a quality gate.

---

## What It Gets Right

**Quality-gate-before-write.** Liu et al.'s filtering pipeline is the direct basis for
`synthesis.py`: generate via LLM → judge via separate model → discard if any dimension < 3
→ write. Without the filter, Liu et al. demonstrate that low-quality synthetic tasks corrupt
the training partition. Our judge_score field (input_coherence ≥ 3, ground_truth_verifiability
≥ 3, rubric_clarity ≥ 3) operationalises this directly.

**Binary rubric over continuous scores.** The paper argues that synthetic data's value in
evaluation is strongest when the rubric has *verifiable* correct answers. "Factuality
evaluation aims to ensure consistency of knowledge in the AI system's output with the
knowledge provided by its training data." This is the rationale for our binary 0/1 rubric
dimensions rather than continuous scores — verifiability is the design constraint, not
granularity.

**Four-mode construction.** Liu et al. validate a mixed-source approach (trace-derived,
rule-based, LLM-synthesis, human-authored) as consistent with best practice for small
seed corpora. Their evidence shows that no single generation mode dominates across all
failure types.

---

## Disagreement: Liu et al.'s Quality Conditions Do Not Capture Rubric-Fidelity Failures

Liu et al.'s three quality conditions — factuality, fidelity, unbiasedness — are defined
for general-purpose training data. They do not anticipate the specific failure mode that
matters most for benchmark construction: *rubric-fidelity*, where the synthetic task's
enrichment signals and the injected candidate output are internally inconsistent in a way
that makes the rubric unapplicable.

**Our evidence:** After scoring the train partition, `confidence_hedging` achieved a mean
of 0.439 — the lowest of the five rubric dimensions by a wide margin. The cause: the
programmatic injectors generate candidate emails that fail on hedging, but approximately
56% of tasks have `icp_confidence=low` or `low_peer_count=True` in the enrichment_brief,
meaning the rubric *requires* hedging language that the injected email does not contain.
These tasks are formally correct under Liu et al.'s three conditions — they contain no
false claims, they reflect the distribution of outreach failures, and they are not
systematically biased toward one segment. But they are pedagogically weak: the model
cannot learn "when to hedge" if half the training tasks simultaneously show a hedging
failure and provide a brief where hedging is required. The signal is present; the failure
is the *co-occurrence pattern*, not any of Liu et al.'s three quality dimensions.

Liu et al.'s framework would not catch this. Their quality gates check facts and
distribution; they do not check whether the (brief, candidate, rubric) triple is
internally coherent as a learning signal. For benchmark construction — as opposed to
general SFT data — a fourth condition is needed: *rubric coherence* (the task's ground
truth must be derivable from its inputs without ambiguity). This is the condition our
judge filter targets with `ground_truth_verifiability`, but Liu et al. do not name it.

---

## Net Position

Liu et al. validates the overall construction approach and the filter architecture. The
paper's three quality conditions are necessary but not sufficient for benchmark tasks —
rubric coherence is a fourth condition the paper does not anticipate. For v0.2, the
programmatic generator should enforce `hedging_required=True` tasks only when the
enrichment_brief unambiguously signals low confidence, and inject candidate emails that
make the hedging omission unambiguous.
