# Business-case template

Ask first. Ranges, not points. Every number traceable to a tagged input.

```markdown
# Business case: {decision, named — "Invest 3 engineer-quarters in unified agent view"}

## The ask (≤40 words)

Approve **{option}** — {cost range, loaded} — expected {headline benefit range},
payback {range}. Decision needed by **{date}** because {what the deadline forfeits}.

**Decider:** {role} · **Author:** {role} · **Date:** {YYYY-MM-DD}

## The problem, priced

{2–3 sentences: what the status quo costs per month, in units the decider budgets
in (FTE-hours, churn, incidents, $). Inputs tagged [data:…] / [reported:…] / [estimate].}

## Options

| | Option 0: do nothing | Option A: {…} | Option B: {…} |
|---|---|---|---|
| Build cost | — | {range, loaded, incl. ramp + integration tail} | {range} |
| Run cost (annual, yr 2+) | {status-quo ongoing cost} | {infra + licenses + maintenance} | {…} |
| Opportunity cost | {what worsens by deferring} | {the displaced work, named} | {…} |
| Headline benefit | 0 (baseline) | {range + confidence} | {range + confidence} |
| Time to value | — | {range} | {range} |
| Champion-able? | yes — {who'd argue it} | yes — {…} | yes — {…} |

## Benefit calculations (re-runnable)

### {Benefit 1, Option A}
- Formula: {inputs → output}
- Inputs: {value [data: source]} × {value [estimate]} × …
- Result: **{range}** · Confidence: {high|medium|low} — {why}

{Repeat per material benefit. A benefit with no calculation block doesn't appear in the option table.}

## Sensitivity — the flip-assumption

**The recommendation flips if:** {single input + the threshold — "agent adoption < ~40%"}
**Confidence on that input:** {tag} → **De-risking step:** {pilot / staged commit / data pull, with cost and duration}
{If no single input flips it, name the pair that does.}

## Recommendation (one option)

**{Option}.** {Two sentences of reasoning.}
**What we give up:** {the runner-up's strongest point, stated fairly.}
**Conditions:** {the de-risking step above; any staging of the commitment.}

## Risks beyond the numbers

- {execution/organizational/vendor risk} — {mitigation or acceptance, one line each}

## Not in this case

{What was deliberately excluded from the math (unquantifiable strategic upside,
morale, …) — named so the decider can weigh it qualitatively, not smuggled into the numbers.}
```
