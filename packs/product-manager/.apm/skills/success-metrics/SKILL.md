---
name: success-metrics
description: Define how a feature's success will be measured before it's built — one primary metric with target, timeframe, and baseline; guardrail and counter-metrics; an instrumentation plan naming every event; and a pre-committed decision rule for what happens if the target is missed. Use when the user asks "how do we know this worked", needs KPIs or success criteria for a feature, or wants a measurement/instrumentation plan before launch.
---

# success-metrics

Answers "how will we know it worked?" *before* build, when the answer can still change what gets built — and makes the measurement honest by pre-committing the decision rule, naming the counter-metric that catches gaming, and writing the instrumentation plan so launch day isn't the day someone discovers no event fires. Expands the one-line success criteria in a `prd-draft` into the full measurement design.

## How to respond

1. **Extract the goal** from the PRD, brief, or conversation. Ask at most 2 questions, spent on **baseline** ("what's the number today, and where does it live?") and **decision authority** ("who acts if the target is missed?"). No goal articulated yet → stop and route to `prd-draft`; metrics for an unstated goal measure noise. Non-interactive run (no user to ask): a stated-but-vague goal gets sharpened and tagged `[assumption]`; no goal at all → emit `BLOCKED: need the feature's goal` — never invent one.

2. **Pick exactly one primary metric.** More than one primary means none — when they diverge, nobody pre-agreed which wins. The primary is an **outcome the user experiences or the business banks**, not an output the team ships. ✅ *"Median support-ticket handle time"* — ❌ *"Number of dashboard features launched"* — ❌ *"Dashboard page views"* (attention is not outcome). Every other contender becomes a secondary, guardrail, or gets cut.

3. **Give the primary its three numbers**: **baseline** (today's value + source; if unknown, the first milestone of the plan is *measuring it* — a target without a baseline is a guess about a guess), **target** (the value that means "worked"), **timeframe** (when judged, plus the patience window — how long after launch before the data is trusted: novelty effects, weekly cycles, cohort maturity).

4. **Add leading indicators** — 2–3 metrics that move within days and plausibly predict the primary, each with its causal sentence: ✅ *"% of tickets where the agent opens the unified view — if agents don't adopt it, handle time can't drop"*. Leading indicators are for steering mid-flight; only the primary decides success.

5. **Set guardrails and the counter-metric.** Guardrails: 2–4 things the feature must **not** degrade (error rate, page latency, adjacent-flow conversion, support volume), each with its current value and an alert threshold. For a **brand-new surface with no prior value** (e.g. the feature's own latency), the guardrail says "baseline measured in week 1, threshold set then" — the same escape hatch the primary metric gets; don't invent a current number that can't exist pre-launch. Counter-metric: the specific way the primary could be gamed, and the metric that catches it — ✅ *"Handle time could drop via premature ticket closure → watch reopen rate"*. A primary without a counter-metric invites exactly the behavior it can't see.

6. **Write the instrumentation plan** — for every metric: the event name (consistent scheme, e.g. `domain.object.action`), its properties (incl. the dimensions you'll slice by: tenant, plan, platform), where it fires, and whether it **exists today or must be built**. The must-build list is a launch dependency, not a fast-follow: shipped-then-instrumented features have no week-one data and a contaminated baseline. Dashboard owner and review cadence named.

7. **Pre-commit the decision rule.** One sentence, agreed before launch, naming the action: ✅ *"If primary improvement < 10% at day 60 with ≥70% agent adoption, we run the iteration review; < 10% with low adoption, we fix adoption first; guardrail breach at any point pauses rollout"*. Without it, every result becomes an argument and every miss becomes "directionally positive."

8. **Emit with [`templates/metrics-plan.md`](templates/metrics-plan.md)** in one message: metric tree (primary → leading → guardrails/counter), the three numbers, instrumentation table, decision rule, and review cadence.

## Useful references in this skill

- [`templates/metrics-plan.md`](templates/metrics-plan.md) — the metric tree, instrumentation table, and decision-rule skeleton

## Quality bar

- **Exactly one primary metric**, and it's an outcome, not an output or a vanity count. The doc states why it was chosen over the runner-up.
- **Baseline, target, timeframe all present** — or "measure baseline" is explicitly milestone 1. No target hangs in the air.
- **Every metric maps to a named event** marked exists/must-build. A metric without an event is fiction with a chart placeholder.
- **The counter-metric names the gaming path.** "Could this number improve while the user's life gets worse?" has a written answer.
- **The decision rule is action-shaped and pre-committed** — who does what at which threshold — not "we'll review the data".
- **Guardrails have current values and alert thresholds**, so "don't degrade X" is checkable, not sentimental.

## When to use this skill

- ✅ A PRD's goals need their full measurement design
- ✅ "How do we know this feature worked?" / "define the KPIs for X"
- ✅ Pre-launch instrumentation planning — what events must exist on day one
- ✅ Retro-fitting honest metrics onto a feature that shipped without any

## When NOT to use this skill

- ❌ No goal exists yet — `prd-draft` first; metrics can't rescue an unstated goal
- ❌ Org/quarterly OKR setting — this skill measures one feature, not a company
- ❌ Analyzing results after the fact — this designs the measurement; analysis is a conversation with the data
- ❌ A/B-test statistics (power, sample size) — name the need, hand to the data team; don't improvise math

## Anti-patterns to avoid

- ❌ **Twelve "key" metrics.** A dashboard where everything is key lets every outcome be declared a win. One primary; the rest serve it.
- ❌ **Targets without baselines.** "Increase activation to 40%" — from what? If today is 38%, the feature is a rounding error wearing a goal.
- ❌ **Vanity metrics as primary.** Page views, sign-ups, sessions — countable, reportable, and silent on whether anyone's life improved.
- ❌ **Instrumentation as fast-follow.** "We'll add tracking next sprint" = no week-one data, contaminated baseline, and a success debate held on vibes.
- ❌ **Post-hoc decision rules.** Deciding what the numbers must show *after* seeing them — the moment measurement becomes marketing.
- ❌ **Ignoring the patience window.** Judging at day 7 what needs a 60-day cohort — novelty spikes and weekly cycles read as signal.
- ❌ **Proxy laundering.** Using clicks as a proxy for value and then forgetting it's a proxy — label proxies as proxies, every time they're cited.
