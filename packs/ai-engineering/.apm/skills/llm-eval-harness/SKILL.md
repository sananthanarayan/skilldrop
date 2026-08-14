---
name: llm-eval-harness
description: Design an evaluation harness for an LLM-powered feature — a versioned golden set (representative + adversarial + regression cases), the cheapest adequate grading method per case, a metric with a pre-set pass bar and regression gate, and a failure taxonomy that targets iteration. Use when the user is building or tuning an LLM feature (prompt, RAG, agent, classifier) and needs evals, a way to test prompt/model changes, or to stop shipping quality regressions on vibes.
---

# llm-eval-harness

Builds the measurement that turns "the new prompt feels better" into "the new prompt scores 0.91 vs 0.84 baseline, with zero regressions on the critical subset." Without it, every prompt or model change is a vibe with a deploy button. Provider-neutral by design — the harness shape is the same whether the feature runs on Claude, GPT, Gemini, or a local model; only the runner differs. Distinct from `ai-usage-report` (telemetry after the fact) and `success-metrics` (product outcomes) — this is the **dev-loop quality gate**.

## How to respond

1. **Pin the task and the unit of judgment.** What does the feature do (classify / extract / summarize / answer-with-RAG / agentic-multi-step), and **what does one gradeable output look like**? Ask at most 2 questions, spent on the failure that hurts most ("what's a wrong answer that would actually cause a problem?") and whether ground truth exists. The answer-that-hurts shapes the adversarial cases and the critical subset.

2. **Build the golden set with three deliberate buckets** (case format in [`templates/`](templates/)):
   - **Representative** — the real distribution of inputs, sampled from production/logs where possible, not invented. This sets the headline number.
   - **Adversarial / edge** — the inputs that break things: ambiguous, out-of-scope, prompt-injection attempts, empty/malformed, the long tail. This is where models actually differ.
   - **Regression** — every past failure, frozen as a case the moment it's fixed, so it can never silently return.
   Size honestly: **50 real, well-labeled cases beat 5,000 synthetic ones.** State the count per bucket and how cases were sourced; a golden set of model-generated inputs graded by a model is a hall of mirrors, not an eval.

3. **Choose the cheapest adequate grading method per case** (decision tree in [`reference.md`](reference.md)) — descending order of preference, because cheaper means faster, deterministic, and trustworthy:
   - **Programmatic / exact** — string/JSON match, regex, schema validation, numeric tolerance. Use wherever the output is checkable. Free and non-negotiable when applicable.
   - **Structured assertions** — "contains X", "cites a real source from the context", "valid JSON with field Y in range". Deterministic checks on unstructured output.
   - **LLM-as-judge** — only when quality is genuinely subjective (helpfulness, tone, faithfulness). And when used, the judge gets its **own rubric, its own validation against human labels, and controls for its known biases** (position, verbosity, self-preference). An unvalidated judge is an opinion you've automated.

4. **Set the metric and the pass bar before running anything.** Per-case pass/fail or score, then the aggregate (accuracy, F1 for imbalanced classes, mean rubric score — pick the one that matches the task, not the flattering one). **Define the regression gate now**: the suite must not drop below baseline on the headline metric, AND the **critical subset must stay at 100%** (the answers-that-hurt are pass/fail, not averaged-away). A gate set after seeing results is a rationalization.

5. **Define the failure taxonomy** — the categories you'll bucket failures into (hallucination, format violation, refusal, missed-edge-case, instruction-ignored, …) so iteration targets the **biggest bucket** instead of the most recent annoyance. The taxonomy turns a score into a to-do list.

6. **Add the guardrails quality can't see.** Cost per eval run and per-output, p95 latency, and token usage — tracked alongside the quality metric so a +2% quality change that doubles cost or latency is a visible tradeoff, not a surprise invoice. (Mirrors `success-metrics`' counter-metric discipline.)

7. **Write the iteration loop.** Versioning: the golden set, the prompts, and the judge rubric are versioned **together**; every prompt/model change re-runs the full suite before merge. State the anti-leakage rule explicitly: **you tune on a dev split and report on a held-out split** — tuning until the eval set passes is overfitting to the test, the oldest mistake in ML wearing a prompt-engineering costume.

8. **Emit with [`templates/eval-plan.md`](templates/eval-plan.md)** in one message: task + unit, golden-set composition table, per-bucket grading method, metric + gate, failure taxonomy, guardrails, and the iteration/versioning rules. Where a runner exists (the user's framework or a simple script), point at it; don't reimplement one.

## Useful references in this skill

- [`reference.md`](reference.md) — the grading-method decision tree, LLM-judge validation + bias controls, and the eval pitfall catalog
- [`templates/eval-plan.md`](templates/eval-plan.md) — the plan skeleton
- [`templates/golden-case.jsonl`](templates/golden-case.jsonl) — the case record format (input, expectation, bucket, grading method, critical flag)

## Quality bar

- **Golden cases are real and labeled, sourced honestly.** Count per bucket stated; synthetic-input + model-graded sets are flagged as the weak evidence they are.
- **Each case names its grading method, and the cheapest adequate one was chosen.** LLM-judge is the exception that justifies itself, not the default.
- **The metric and both gates (no-regression + critical-subset-100%) are set before the first run.** Post-hoc bars don't count.
- **LLM-judges are validated against human labels and bias-controlled.** An unvalidated judge score is presented as such.
- **A held-out split exists and the no-tuning-on-test rule is stated.** Reporting the number you optimized against is the cardinal eval sin.
- **Cost and latency are tracked beside quality**, so quality gains that blow the budget are visible.

## When to use this skill

- ✅ Building or tuning an LLM feature (prompt, RAG, agent, classifier) and need to measure quality
- ✅ "How do we test this prompt/model change without shipping a regression?"
- ✅ Setting up a regression gate before iterating on prompts
- ✅ A subjective-quality feature where you're about to reach for an LLM judge — design it right

## When NOT to use this skill

- ❌ Tabulating AI usage/adoption telemetry — that's `ai-usage-report`
- ❌ Product-outcome metrics for a feature (adoption, handle time) — that's `success-metrics`
- ❌ Picking which model/vendor to use — that's `tech-comparison-matrix`
- ❌ The provider-specific API mechanics (token counting, streaming, tool-call format) — consult the provider's own reference; this skill is the eval methodology

## Anti-patterns to avoid

- ❌ **Vibe-tuning.** Changing the prompt until the three examples you keep pasting look good. Three cases isn't an eval; it's confirmation bias with a text box.
- ❌ **The synthetic hall of mirrors.** Model-generated inputs graded by a model — measures whether the model agrees with itself, not whether it's right.
- ❌ **LLM-judge as the default grader.** Reaching for a judge where a regex would do: slower, costlier, non-deterministic, and unvalidated. Earn the judge.
- ❌ **Tuning on the test set.** Iterating until the eval passes, then reporting that number. The held-out split exists precisely to stop this.
- ❌ **Averaging away the critical failures.** 95% aggregate looks great while the 5% that fails is "delete the user's data". Critical subset is 100%-or-fail, never averaged.
- ❌ **Post-hoc pass bars.** Setting the threshold after seeing the score so the result clears it. The bar is a pre-registration, not a retrofit.
- ❌ **Quality-only scoring.** A 1% quality gain that triples latency and cost ships as a win because nobody measured the other two.
- ❌ **The frozen eval set.** A golden set that never grows while the product does — every new production failure must become a new regression case or the eval rots.
