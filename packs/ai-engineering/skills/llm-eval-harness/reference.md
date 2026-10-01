# llm-eval-harness reference — grading decision tree, judge validation, pitfalls

## Grading-method decision tree (cheapest adequate wins)

Walk top to bottom; stop at the first method that can actually judge the output. Most cases never reach the LLM judge.

```
Is the output exactly checkable (a label, a number, valid JSON, a known answer)?
  → PROGRAMMATIC: exact match / regex / schema validation / numeric tolerance.
    Deterministic, free, instant. Use it.

Else: is correctness checkable by deterministic rules on free text?
  (contains required fact, cites a source present in the context, no forbidden
   content, field in range, format constraints hold)
  → STRUCTURED ASSERTIONS: a list of boolean checks per case.
    Still deterministic. Combine several for partial credit.

Else: is quality genuinely subjective?
  (helpfulness, tone, faithfulness to source, reasoning quality, "is this a good summary")
  → LLM-AS-JUDGE — but only after the validation below. Not before.
```

Programmatic + structured should cover the majority of cases for classify/extract/format tasks. If you're reaching for a judge on a classification task, you probably haven't defined the labels tightly enough.

## LLM-as-judge: the rules that make a judge trustworthy

A judge is a model grading a model. Untreated, that's an opinion with a confidence problem. Required before its scores count:

1. **Give it a rubric, not a vibe.** Explicit criteria, a scoring scale with anchored descriptions per point ("3 = answers fully and cites correctly; 2 = answers but a citation is wrong; 1 = …"). "Rate 1–5" with no anchors produces noise.
2. **Validate against human labels.** Hand-label 30–50 cases; run the judge; measure agreement (accuracy / correlation / Cohen's κ). If the judge disagrees with humans, fix the rubric or don't trust the judge. Re-validate when the rubric changes.
3. **Control known biases:**
   - **Position bias** (pairwise) — judges favor the first (or second) option. Randomize order; run both orders and require agreement.
   - **Verbosity bias** — judges rate longer answers higher. Watch for it; penalize padding in the rubric.
   - **Self-preference** — a judge favors outputs from its own model family. Prefer a different model as judge than the one under test where feasible.
   - **Sycophancy** — leading prompts ("isn't this a great answer?") inflate scores. Keep the judge prompt neutral.
4. **Prefer binary/low-cardinality judgments.** "Faithful: yes/no" is more reliable and more reproducible than "rate faithfulness 1–10."
5. **Report judge cost and latency** — it's part of the eval's running cost, often the dominant part.

## Metric choice (match the task, not the flattering number)

| Task | Metric | Why not accuracy |
|---|---|---|
| Balanced classification | accuracy | fine |
| Imbalanced classification | F1 / precision+recall per class | accuracy hides minority-class failure |
| Extraction | field-level precision/recall | one number hides which fields fail |
| Retrieval (RAG) | recall@k, MRR + faithfulness | answer can be right by luck with bad retrieval |
| Open generation | rubric mean + critical-subset pass-rate | aggregate alone averages away the harms |
| Agentic / multi-step | task-completion rate + per-step validity | end-success hides a broken middle step |

## Eval pitfall catalog

- **Test-set leakage** — tuning prompts against the same cases you report on. Split dev/held-out; report only held-out.
- **Goodhart / metric-gaming** — the metric improves while the behavior worsens (e.g. always-refuse scores high on a "no-harmful-output" metric). The critical subset and a counter-metric catch it.
- **Distribution skew** — golden set doesn't match production inputs, so the score is about a world that doesn't exist. Sample from real logs.
- **Judge drift** — the judge model changes underneath you (provider updates it) and scores shift with no prompt change. Pin the judge model/version; re-baseline on change.
- **Frozen eval rot** — product evolves, eval doesn't; the score stays green on yesterday's product. New failure → new regression case, always.
- **Single-run noise** — non-zero temperature makes one run unrepresentative. Fix temperature for eval, or run N times and report variance.
- **Aggregate myopia** — celebrating 94% while a critical 6% silently fails. Always slice by bucket and by critical flag.
