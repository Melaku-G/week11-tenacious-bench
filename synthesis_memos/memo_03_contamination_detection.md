# Synthesis Memo 03 — Benchmark Contamination: Static vs Dynamic Evaluation

**Paper:**
- Chen et al. (2025). *Benchmarking Large Language Models Under Data Contamination:
  A Survey from Static to Dynamic Evaluation.* EMNLP 2025.
  (Authors: Simin Chen, Yiming Chen, Zexin Li, et al. — Columbia University, NUS, UC Riverside)

**Written by:** Tenacious-Bench authoring team
**Date:** 2026-04-28
**Relevance to project:** Direct foundation for the contamination protocol in
`bench/methodology.md` and the five checks in `bench/contamination_check.json`.

---

## Core Argument of the Paper

Chen et al. survey how LLM benchmarking has evolved from *static* to *dynamic* evaluation
in response to growing contamination risk. Their central claim: **static benchmarks are
inherently vulnerable as training datasets grow, and the field should shift toward dynamic
methods** — those that either refresh tasks after a model's training cutoff (temporal
cutoff) or regenerate tasks algorithmically to prevent memorisation (rule-based or LLM-based
transformation).

The paper introduces a unified evaluation framework for dynamic benchmarks with six criteria:
**correctness, scalability, collision, stability of complexity, diversity,** and
**interpretability**. The most novel criterion is *collision*: if a dynamic benchmark's
generation algorithm is public, a model trained on that algorithm's outputs can still game
the benchmark. The paper argues that collision-resistance should be a first-class design goal.

Static mitigation methods (canary strings, label encryption, post-hoc n-gram detection) are
covered in Section 3 and dismissed as "inherently limited" because they cannot verify actual
training-set exposure — a closed-source model may have seen the data regardless of what the
evaluator put in its test set.

---

## Where the Paper Is Right and How It Shaped Our Choices

**On post-hoc detection:** Chen et al.'s taxonomy of static detection methods directly
informed our `contamination_check.json` choices:

| Chen et al. method | Our implementation |
|-------------------|-------------------|
| Direct overlap detection (n-gram) | CC-001, CC-003: 8-gram threshold across partition boundaries |
| Input deduplication | CC-004: SHA-256 hash of enrichment_brief |
| Temporal verification | CC-005: authored_date check; held-out sealed post-generation |
| Embedding similarity | CC-002: cosine <0.85 (pending — requires Colab Day 4) |

**On rule-based generation limitations:** The paper notes that "publicly available
rule-generated data may increase the risk of in-distribution contamination during training."
This is a real concern for `programmatic.py` — the injected failure templates (e.g.
`inject_fc3_overclaim`) produce predictable phrases. We accept this risk for the training
partition but it is why the held-out partition was sealed before the generation scripts were
committed publicly.

---

## Where I Disagree: Dynamic Benchmarking Is the Wrong Goal for Domain-Compliance Evaluation

Chen et al.'s primary recommendation is to move toward dynamic benchmarks. For a
general-purpose capability benchmark (MMLU, HumanEval, GSM8K) this is well-motivated:
the failure modes the benchmark tests are stable but the *instances* can be refreshed.

For Tenacious-Bench, this recommendation is wrong in two ways:

**1. The rubric is the benchmark, not the task instances.**
Tenacious-Bench evaluates whether an agent correctly applies five domain rules: no unsupported
growth claims, no AI pitch below maturity threshold, no banned phrases, appropriate hedging,
correct format. These rules come from a brand guide that does not change month-to-month.
A dynamic approach — regenerating tasks with new company names or paraphrased briefs — does
not change what the benchmark tests. The "contamination" Chen et al. worry about is
memorisation of *task instances*; what Tenacious-Bench guards against is memorisation of
*failure patterns*, which is actually the learning we want from SFT.

**Evidence from our data:** The CC-001 n-gram check flagged all 230 train tasks as
overlapping with held-out because the injection templates share phrases across partitions.
But CC-004 (enrichment_brief hash) returned 0 collisions — the *inputs* are unique. A model
trained on train tasks that encounters a held-out task with a novel company and novel brief
must apply the rubric to genuinely new input. That is exactly what we want to measure.
Chen et al.'s dynamic framing would treat the template overlap as a contamination failure;
our evidence shows it is not.

**2. Dynamic regeneration breaks machine-verifiability.**
Our scoring evaluator works because rubric dimensions are machine-checkable against exact
patterns: `[DRAFT]` in subject, specific banned phrases, word count ≤ 120, segment gate
condition. A dynamically regenerated task that paraphrases "rapidly scaling" as "growing
at pace" would still violate signal fidelity but the keyword check would miss it. Dynamic
methods work for tasks with verifiable ground truth (math, code). They do not work for
tone compliance or brand guide adherence — the scoring evaluator's precision depends on
the rubric and the template, not on dynamic instance regeneration.

Chen et al. acknowledge this implicitly: their survey focuses almost entirely on math,
code, and factual QA benchmarks. Instruction-following benchmarks (the closest analogue
to Tenacious-Bench) are listed in their taxonomy but receive no dynamic treatment. The
paper's recommendations apply to a domain where ground truth can be regenerated
algorithmically; Tenacious-Bench's ground truth is grounded in a specific brand voice
that cannot be regenerated.

---

## What the Paper Adds That General Contamination Checks Miss

**The collision criterion.** Chen et al. define collision as: to what extent can a model
trained on the dynamic benchmark's outputs still game the benchmark? For Tenacious-Bench
this translates to a different question: if Qwen2.5-1.5B is SFT-trained on the train
partition and then evaluated on held-out, is the improvement we observe generalisation or
pattern memorisation?

The collision concern points to a real gap in our ablation design. If the 20 company
templates appear across all partitions, a model may improve on held-out simply by learning
"NeuralEdge Analytics → don't over-claim" rather than learning "low open_roles_estimate →
don't over-claim." The ablation needs to report pass rates stratified by whether the company
appears in the training set — a check Chen et al.'s collision criterion anticipates but
which is not in the current `ablation_results.json`.

**Static enhancement methods we did not implement.** The paper covers label protection
(withholding gold labels from public access) and canary strings (injecting unique marker
tokens to detect verbatim memorisation). Neither is practical for Tenacious-Bench at this
scale, but the canary-string idea could be adapted: including a unique UUID in each
held-out task's enrichment_brief would let us detect verbatim memorisation in the SFT
output logs.

---

## Net Position

For Tenacious-Bench v0.1, Chen et al.'s survey validates our n-gram + hash + time-shift
approach as grounded in the detection literature. The recommendation to adopt dynamic
benchmarking is explicitly rejected for this domain: our rubric is bound to a stable brand
guide, our scoring evaluator requires fixed patterns, and our evidence (CC-004, zero
enrichment collisions) shows the actual contamination risk is input-level leakage, which
our checks address. The collision criterion Chen et al. introduce is the one contribution
we should act on — it surfaces a company-name confound in the ablation that should be
stratified out in `ablation_results.json`.
