---
name: agent-budget
description: Write the spend spec for an agentic workflow — per-stage model tiers, token caps with hard abort rules, a graceful-degradation order, and cost-per-outcome as the governing metric. Use when the user asks what an agent loop or multi-agent workflow should be allowed to spend, wants token/cost budgets and caps for AI automation, or got a surprise bill from an agent fleet.
---

# agent-budget

An unbudgeted agent loop is a runaway-cost incident with an architecture diagram. This skill produces the **budget spec** that governs an agentic workflow: what each stage may spend, on which tier of model, what happens at the cap, and — the number that actually matters — what one *outcome* costs. Pairs with `agent-loop-design` (the caps land in its loop spec) and `subagent-design` (the fleet line lands in its role cards); the tier vocabulary is this repo's own light/standard/heavy routing abstraction, so the spec ports across providers. Infra spend (compute, storage, egress) is `capacity-cost-model`'s domain — this skill budgets the tokens.

## How to respond

1. **Pin the outcome unit and the workflow's stages.** Ask at most 2 questions, spent on: *"what is one successful outcome?"* (a merged PR, a triaged ticket, a verified report — the denominator every cost divides by) and *"what does a typical run look like today?"* (stages, rounds, models — or "not built yet", which makes this a design-time budget, the cheap time to write one). Non-interactive run (no user to ask): derive both from the input and tag `[assumption]`; no outcome unit derivable → emit `BLOCKED: need the workflow and its outcome unit`.

2. **Assign each stage the cheapest adequate tier** — light / standard / heavy, per the routing rule of thumb: **light** for mechanical extraction and formatting, **standard** for most generation, **heavy** only where the hard thinking *is* the value (adversarial verification, weighted judgment) — and heavy stages are never downgraded to save money; they're where the money buys correctness. Every tier assignment carries a one-line rationale. The classic misallocation runs both directions: frontier models formatting JSON, and — worse — the cheap model doing the verify pass that exists to catch the cheap mistakes.

3. **Set three numbers per stage** in [`templates/budget-spec.md`](templates/budget-spec.md): **expected** spend per run (estimate honestly, tag `[assumption]` until measured), **cap** (the hard stop — 3–5× expected, tighter for unattended loops), and **on-cap action** (abort-and-escalate, or degrade — never "continue and warn"; a warning nobody is watching is a continue). State each as tokens **and** approximate money — tokens are what the harness enforces, but money is the only unit that sums across tiers, so **all cap comparisons happen in currency**. A stage that fans out per item carries two caps: a per-item cap (that item fails to the report's needs-human list; the rest continue) and a stage-wide cap. Then the **run-level cap** for the whole workflow — in currency, *less* than the sum of stage caps: every stage simultaneously hitting its cap is not a run to finish, it's an anomaly to stop.

4. **Write the degradation ladder** — what gives, in order, when spend pressure hits: first **narrow scope** (fewer items per run), then **reduce parallelism** (smaller fleet, slower wall-clock), then **cut non-verification stages** (skip the polish pass), and **last — never — verification**. Skipping verify to save tokens converts a cost problem into a correctness problem at the exact moment quality is already under pressure; a workflow that can't afford its verifier can't afford to run. State each rung's trigger and who flips it.

5. **Make cost-per-outcome the governing metric.** Total tokens is noise; **spend ÷ successful outcomes** is the number with meaning — a loop that gets cheaper per run but passes fewer runs got more expensive. Give it a target and a review threshold, and put beside it the **comparison line**: what the same outcome costs today (an hour of an engineer's time, the manual process) — a $4 triaged ticket is expensive against 60 seconds of a human's glance and cheap against twenty minutes of one; without the line, nobody can say which.

6. **Add measurement and emit.** Spend logged per run per stage (tagged by stage name, feeding the loop spec's telemetry row); weekly review of cost-per-outcome and cap-hit counts by a named role; alert on cap-hit rate rising (the leading indicator of drift — inputs grew, a prompt regressed, or a model changed under you) and on any run breaching the run-level cap (that's an incident, not a line item). Emit the spec in one message: stage table, run cap, degradation ladder, cost-per-outcome with comparison line, measurement plan. Flag every `[assumption]` estimate as the calibration backlog — after ~20 real runs, expected values stop being guesses. Hand off: the caps → `agent-loop-design`'s loop spec; per-agent tiers → `subagent-design`'s role cards; the verifier's quality gate → `llm-eval-harness`.

## Useful references in this skill

- [`templates/budget-spec.md`](templates/budget-spec.md) — stage table, degradation ladder, cost-per-outcome, and measurement skeleton

## Quality bar

- **The outcome unit is named** and every cost in the doc divides by it.
- **Every stage has tier + rationale + three numbers** (expected, cap, on-cap action). No stage rides free.
- **Heavy tiers survive.** No verification or judgment stage was downgraded to make the total look better.
- **Caps are hard.** Every on-cap action is abort or degrade — "warn and continue" appears nowhere.
- **The run cap is less than the sum of stage caps**, and the doc says why.
- **Verification is last on the degradation ladder**, explicitly.
- **The comparison line exists** — cost-per-outcome sits next to what the outcome costs without the agents.
- **Estimates are tagged.** `[assumption]` until measured; the calibration step is scheduled, not implied.

## When to use this skill

- ✅ "What should this agent workflow be allowed to spend?" — at design time, the cheap time
- ✅ A surprise token bill arrived — retrofit caps and a degradation ladder
- ✅ An `agent-loop-design` or `subagent-design` spec needs its budget line filled in
- ✅ "Is this automation actually cheaper than doing it by hand?" — build the comparison line

## When NOT to use this skill

- ❌ Infra/cloud cost modeling (compute, storage, egress) — `capacity-cost-model`
- ❌ Choosing a model tier for a single skilldrop skill — that's `model-routing.json`'s table, already decided
- ❌ Designing the loop or the fan-out itself — `agent-loop-design` / `subagent-design`; this skill prices what they draw
- ❌ Negotiating provider contracts or rate limits — procurement, not a spec

## Anti-patterns to avoid

- ❌ **Budget-free loops.** "We'll see what it costs" means the invoice is the monitoring system.
- ❌ **Warn-and-continue caps.** A cap whose breach action is a log line is a number, not a cap.
- ❌ **Skimping the verifier.** Downgrading or skipping verification under spend pressure — the false economy that ships fleet-speed garbage precisely when scrutiny dropped.
- ❌ **Token vanity metrics.** Celebrating "20% fewer tokens" while cost-per-successful-outcome rose because pass rates fell.
- ❌ **Frontier-everything.** The orchestrator's model formatting JSON at heavy-tier prices because nobody assigned tiers per stage.
- ❌ **Missing comparison line.** A cost-per-outcome with nothing beside it can justify anything or condemn anything.
- ❌ **Estimates that never graduate.** `[assumption]` numbers still governing caps six months and a thousand runs later.
