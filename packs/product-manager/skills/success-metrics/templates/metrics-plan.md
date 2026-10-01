# Metrics-plan template

One primary. Everything else exists to steer toward it or to catch it lying.

```markdown
# Success metrics: {feature}

**Goal (from PRD):** {the outcome this feature exists to cause}
**Decision authority:** {role who acts on the decision rule} `[reported]`

## Primary metric (exactly one)

**Metric:** {outcome the user experiences or the business banks}
**Why this over {runner-up}:** {one sentence}
**Proxy?** {no | yes — proxy for {real outcome}; label it as proxy wherever cited}

| Baseline | Target | Judged at | Patience window |
|---|---|---|---|
| {value + source, or "MILESTONE 1: measure baseline by {date}"} | {value} | {date / days post-launch} | {why not earlier — novelty, weekly cycle, cohort maturity} |

## Leading indicators (steering only — they never declare success)

| Metric | Moves within | Causal sentence |
|---|---|---|
| {e.g. % agents opening unified view} | days | {if this doesn't move, primary can't} |

## Guardrails (must not degrade)

| Metric | Current | Alert threshold | Action on breach |
|---|---|---|---|
| {error rate / latency / adjacent conversion / support volume} | {value, or "measure wk 1" for a new surface} | {value} | pause rollout / page owner |

## Counter-metric (the gaming catch)

**Primary could be gamed by:** {the behavior}
**Caught by:** {metric + threshold} — reviewed alongside the primary, every review.

## Instrumentation plan (launch dependency, not fast-follow)

| Event | Properties (incl. slice dimensions) | Fires where | Status |
|---|---|---|---|
| `domain.object.action` | {tenant, plan, platform, …} | {surface/service} | exists / **must build** |

**Must-build events are launch blockers.** Dashboard: {where} · Owner: {role} · Review cadence: {weekly until judged-at date}

## Decision rule (pre-committed — action-shaped)

- If {primary condition} at {judged-at} with {adoption/leading condition} → {action}
- If {primary misses} but {adoption low} → fix adoption first, re-judge at {date}
- Guardrail breach at any time → {action}

## Out of scope for measurement

- {what this plan deliberately doesn't measure, and why}
```
