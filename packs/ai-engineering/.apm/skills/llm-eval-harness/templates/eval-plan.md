# Eval-plan template

The plan is the pre-registration: golden set, grading, metric, and gates are decided here, before the first run, so results can't move the goalposts.

```markdown
# Eval plan: {LLM feature}

**Task:** {classify | extract | summarize | RAG-answer | agent}
**Unit of judgment:** {what one gradeable output is}
**The answer that hurts most:** {the wrong output that would actually cause a problem} → drives the critical subset

## Golden set

| Bucket | Count | Sourced from | Notes |
|---|---|---|---|
| Representative | {n} | {prod logs sample / …} | real distribution |
| Adversarial / edge | {n} | {hand-built + injection attempts} | where models differ |
| Regression | {n, grows over time} | {past failures, frozen} | never silently returns |

**Critical subset:** {which cases are pass/fail-at-100%, never averaged}
**Honesty note:** {synthetic %, label provenance — flag weak evidence}
**Split:** dev {n} (tune here) / held-out {n} (report here) — never tune on held-out.

## Grading (cheapest adequate per bucket/case)

| Case type | Method | Detail |
|---|---|---|
| {labeled classification} | programmatic | exact label match |
| {extraction} | structured assertions | field-level checks |
| {open generation} | LLM-judge | rubric below; validated κ={x} vs human labels |

{If LLM-judge used: judge model+version pinned = {…}; bias controls = {position-randomized, binary scoring, neutral prompt}.}

## Metric & gates (set BEFORE running)

- **Headline metric:** {accuracy | F1 | rubric mean | task-completion} — chosen because {matches task}.
- **Baseline:** {current value, or "to be established by first run = baseline"}.
- **Regression gate:** headline metric ≥ baseline AND critical subset = 100%. A merge that breaches either is blocked.

## Failure taxonomy (iterate on the biggest bucket)

| Category | Example | Count last run |
|---|---|---|
| hallucination | … | |
| format violation | … | |
| missed edge case | … | |
| instruction ignored | … | |

## Guardrails (tracked beside quality)

| | Value | Budget |
|---|---|---|
| Cost / 1k outputs | | |
| p95 latency | | |
| Tokens / output | | |

## Iteration & versioning rules

- Golden set + prompts + judge rubric versioned together; bump on any change.
- Every prompt/model change re-runs the full suite on held-out before merge.
- Every new production failure becomes a regression case the day it's found.
- Eval temperature fixed (or N-run with variance reported).
```
