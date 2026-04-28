# Synthesis Memo 04 — LLM-as-a-Judge

**Paper:**
- Gu et al. (2025). *A Survey on LLM-as-a-Judge.* arXiv:2411.15594v6.

**Written by:** Tenacious-Bench authoring team
**Date:** 2026-04-28
**Relevance to project:** Foundation for the judge-filter architecture in `synthesis.py`,
the judge rotation policy in `methodology.md`, and the scoring design in
`scoring_evaluator.py`.

---

## Core Argument

Gu et al. survey the paradigm of using LLMs as evaluators instead of humans. The central
question is reliability: under what conditions can an LLM judge be trusted? Their taxonomy
identifies four failure modes — *position bias* (outputs rated differently based on order),
*verbosity bias* (longer outputs rated higher regardless of quality), *self-enhancement
bias* (models favour outputs resembling their own training distribution), and *preference
leakage* (when the judge and generator share training data, pass rates are inflated).
Reliable LLM judging requires explicit bias mitigation, diverse scoring formats, and
separation of the generation model from the judge model.

---

## What It Gets Right

**Reference-based over reference-free scoring.** Gu et al. argue that LLM judges should
use reference-based scoring (comparing output to a ground-truth criterion) rather than
reference-free scoring (open-ended quality judgement) when the evaluation task has
verifiable dimensions. Our judge prompt in `synthesis.py` gives the rubric explicitly —
this is reference-based. Asking a judge to evaluate tone "in general" would be
reference-free and far less reliable. The rubric-explicit design follows directly from
Gu et al.

**Judge rotation policy.** Gu et al.'s preference leakage finding drove the explicit
decision in `synthesis.py`: `GENERATION_MODEL = "deepseek/deepseek-chat"`,
`JUDGE_MODEL = "qwen/qwen-2.5-72b-instruct"`. A runtime guard raises `SystemExit` if
both are set to the same model family. The paper's guidance is not applied as a
preference — it is enforced as a hard constraint.

**Regex over exact-match for scoring.** Gu et al. note that "rule-based token extraction
methods are inherently brittle." This shaped `scoring_evaluator.py`: banned phrases are
checked via regex (`re.search`, case-insensitive) rather than `str.__contains__` exact
matching. A phrase like "SCALING AGGRESSIVELY" in all-caps would pass an exact-match
check but is correctly caught by the regex.

---

## Disagreement: Gu et al.'s Bias Taxonomy Is Built for Pairwise Comparison — Position
and Verbosity Bias Are Structural Non-Issues for Single-Output Rubric Scoring

Gu et al.'s four bias types are predominantly concerns for *pairwise* evaluation (compare
output A vs output B) or *open-ended* quality scoring (rate this response 1–10). Position
bias and verbosity bias both require a comparison context: position bias assumes the judge
sees two outputs in some order; verbosity bias assumes the judge can trade off length
against quality without an explicit cap.

**Our evidence:** Tenacious-Bench uses single-output, rubric-explicit scoring. Every task
presents one candidate email and asks the judge whether it satisfies five binary conditions.
There is no comparison, so position bias has no mechanism to operate. There is an explicit
word count constraint (≤ 120 words, checked by `format_compliance`), so verbosity bias
cannot inflate scores — a longer email fails, not passes. In our dev partition, 18.7% of
tasks fail `format_compliance`, which is the opposite of verbosity inflation.

More importantly: our Week 10 trace evidence shows the relevant failure is not judge bias
at all. Trace `b2c3d4e5-0001` (FC-3 over-claim, P01) shows the agent wrote "your
engineering team continues to scale rapidly" with `open_roles_estimate=1` and
`engineering_velocity=low`. This failure is *signal-blind* — the model ignored structured
fields it had access to. A judge evaluating this output on signal fidelity does not need
bias mitigation; it needs to check whether the claim is supported by the brief. That is
a lookup, not a judgement. Gu et al.'s bias taxonomy addresses failure modes that arise
from under-specified scoring criteria. Our rubric is explicit enough that the judge's
primary failure mode is rubric misapplication, not bias. The two papers address different
points in the evaluation reliability spectrum.

The practical consequence: for Tenacious-Bench's current scoring evaluator, Gu et al.'s
position and verbosity bias mitigations are irrelevant. Self-enhancement bias and
preference leakage remain relevant (and are addressed by model rotation). Future versions
that add open-ended tone scoring — where a judge must rate "Professional" without a
keyword checklist — will need the full bias-mitigation toolkit Gu et al. prescribe.

---

## Net Position

Gu et al. validates the judge rotation policy and the reference-based rubric design.
Two of the four bias types (position, verbosity) are structural non-issues given our
single-output, rubric-explicit, word-count-capped evaluation design — confirmed by our
trace data and dev partition scoring. Self-enhancement and preference leakage are the
relevant failure modes and are addressed by the DeepSeek/Qwen model separation enforced
at runtime in `synthesis.py`.
