# Synthesis Memo 02 — Datasheets for Datasets and Data Cards

**Papers:**
- Gebru et al. (2021). *Datasheets for Datasets.* Communications of the ACM.
- Pushkarna et al. (2022). *Data Cards: Purposeful and Transparent Dataset Documentation
  for Responsible AI.* FAccT 2022.

**Written by:** Tenacious-Bench authoring team
**Date:** 2026-04-28
**Relevance to project:** Direct foundation for `bench/datasheet.md` and the
documentation standard applied to Tenacious-Bench v0.1.

---

## Core Argument of Each Paper

**Gebru et al.** propose that every ML dataset should be accompanied by a standardised
*datasheet* — a document that answers a fixed set of questions about motivation,
composition, collection process, preprocessing, uses, distribution, and maintenance.
The analogy is the electronics industry datasheet: a component that ships without one
cannot be safely integrated into a larger system. The goal is twofold: give dataset
creators a forcing function for reflection, and give dataset consumers the information
needed to make informed decisions. The paper provides 57 structured questions across
seven sections.

**Pushkarna et al.** argue that Gebru et al.'s framework, while necessary, is not
sufficient in practice. A static document with 57 questions is hard to navigate and
treats all stakeholders identically. They propose *Data Cards* — a layered, user-centric
documentation format with three levels of detail: *telescopic* (executive summary,
one page), *periscopic* (mid-detail, process and provenance), and *microscopic*
(full technical specification, reproducibility-grade). The format is designed to serve
different audiences without requiring them to read all 57 questions.

---

## Where They Agree

Both papers share a foundational claim: **documentation is not optional metadata,
it is the artifact that converts a JSON file into a benchmark.** Gebru et al. state
that "the characteristics of datasets fundamentally influence a model's behaviour"
and that undocumented datasets create invisible failure modes. Pushkarna et al. state
that "a clear and thorough understanding of a dataset's origins, development, intent,
ethical considerations and evolution becomes a necessary step for the responsible
deployment of models."

Both also agree that documentation should cover *decisions and rationales*, not just
facts. It is not enough to say "tasks were generated programmatically." A usable
datasheet explains *why* programmatic generation was chosen, what parameter space
was swept, and what failure modes the generation targets.

---

## Where They Disagree (and Where Pushkarna Improves on Gebru)

**Audience specificity.** Gebru et al. produce a single document for all readers.
A machine learning engineer, a product manager, and an auditor all receive the same
57-question answer sheet. Pushkarna et al. identify this as a practical adoption
barrier: "the burden of understanding often falls on the intelligibility and conciseness
of the documentation." Their layered structure solves this.

**Static vs. living documentation.** Gebru et al. treat the datasheet as a one-time
artifact produced at dataset release. Pushkarna et al. explicitly address the *lifecycle*
of datasets — documentation should evolve as the dataset is updated, split, or used
in downstream models. For Tenacious-Bench, this matters: the held-out partition will
be sealed post-interim and the datasheet should record that event.

**The "purposeful" framing.** Pushkarna et al. add a dimension Gebru et al. omit:
documentation should communicate the *intended use context* with enough specificity
that a consumer can judge fitness for their own task. For Tenacious-Bench, the
intended use context is narrow (B2B sales outreach compliance evaluation), and
the datasheet should state explicitly what the benchmark cannot test — general LLM
quality, customer service resolution, factual QA — so consumers do not apply it
outside its valid scope.

---

## How This Shaped bench/datasheet.md

Gebru et al.'s seven sections provide the structural skeleton. Pushkarna et al.'s
layered framing shaped two additions not in the Gebru template:

1. **Telescopic summary at the top**: one paragraph covering what the dataset is,
   why it was built, and what it cannot grade. A grader or evaluator can stop there
   if they only need the executive view.

2. **Lifecycle events section**: records the held-out sealing date, contamination
   check run date, and version number. Gebru et al. have a "maintenance" section
   but it is forward-looking; Pushkarna et al. emphasise that decisions already
   made should also be documented.

The microscopic level (full field specification, generation script hashes,
partition counts by category) is covered by `schema.json` + `contamination_check.json`
rather than duplicated in the datasheet. The datasheet points to those files rather
than inlining them, consistent with Pushkarna et al.'s linking recommendation.

---

## What These Papers Do Not Cover

Neither paper addresses benchmark construction specifically. Both are focused on
*training and evaluation datasets* for general-purpose models. The key difference
for Tenacious-Bench is that the dataset documents both *inputs* and *candidate
outputs* — the datasheet must document not just how companies were sampled but
also how candidate email outputs were generated (injection templates, synthesis
prompts, adversarial strategies). Gebru et al.'s "collection process" section does
not anticipate this; it assumes human or web-scraped data, not programmatically
injected failure examples.

This gap means `bench/datasheet.md` requires a section that neither template
provides: **failure injection methodology** — what bad behaviours were injected,
by which script, with what seed, and why those behaviours represent the target
failure taxonomy. This is the section most specific to Tenacious-Bench and the
one a grader will scrutinise most carefully.

---

## Net Position

For Tenacious-Bench v0.1, use Gebru et al. for the seven-section structure (it is
the field standard and the challenge requirement). Extend with Pushkarna et al.'s
layered framing — add a telescopic paragraph at the top and a lifecycle events
section. Do not try to merge the two into a single template; treat Pushkarna et al.
as an upgrade to the opening and maintenance sections of the Gebru framework.

The datasheet is the artifact graders will read to decide whether the benchmark
is trustworthy enough to use. It should be written for them, not for the authors.
