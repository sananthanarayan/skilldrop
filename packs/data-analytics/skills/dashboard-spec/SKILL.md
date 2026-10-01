---
name: dashboard-spec
description: Spec a dashboard before anyone builds it — the audience and the decision it serves, the questions in priority order, one chart per question with the chart type and why, the defined metric behind each chart, filters, refresh cadence and freshness SLA, and a list of what is deliberately left off, with vanity metrics cut. Use when the user says "spec a dashboard", "what should go on our KPI dashboard", "the BI team needs requirements for a dashboard", "our dashboard has 40 charts and nobody uses it", or "design the exec dashboard".
---

# dashboard-spec

Writes the one-page brief a BI developer builds from, so the dashboard answers the questions someone actually acts on instead of displaying every number that was easy to query. The spec starts from a decision, not from the available data: who looks at this, how often, and what they do differently depending on what they see. Every chart traces to a question, every question to that decision, and every metric to a written definition. What doesn't trace gets cut, and the cut list is part of the deliverable.

## How to respond

1. **Pin the audience and the decision, asking once.** Ask at most 2 questions in one message: *"Who opens this, and what do they decide or do after looking at it?"* and *"Which metrics already have agreed definitions, and where does the data live?"* If the user gave both, don't ask.

**Non-interactive runs** (subagent, CI, headless): derive the audience and decision from the input and tag them `[assumption]`. A metric with no definition is marked `undefined` in the chart table, not invented. No audience and no decision derivable from the input → emit `BLOCKED: need the audience and the decision this dashboard serves`.

2. **Write the decision statement in one sentence:** who, decides what, how often. ✅ *"Regional support leads decide each Monday which queues get extra staff this week."* — ❌ *"Give visibility into support performance."* If no decision can be named, say so plainly: what the user wants is a report or an archive, and the spec says that instead of designing charts nobody acts on.

3. **List the questions in priority order, at most seven.** Each is a question the audience would ask out loud, paired with the action a bad answer triggers: ✅ *"Which queue is furthest over its response-time target this week? → move staff to it."* Question 1 is the reason the dashboard exists and goes top left. If you have more than seven, the dashboard serves more than one audience; split it.

4. **Give each question exactly one chart, with its type and the reason.** Use the chooser in [`reference.md`](reference.md):
   - change over time → line chart
   - compare categories → bar chart, sorted, starting at zero
   - one current value against a target → number tile with its comparison
   - distribution → histogram or box plot
   - relationship between two measures → scatter plot
   - exact values someone looks up → table

   ✅ *"Sorted horizontal bar, because the question is which queue is worst and a ranked bar answers that at a glance."* No pies for more than three parts, no dual axes, no 3D. Every number tile shows a comparison (against target, last period, or the same period last year). A bare number can't tell anyone whether to act.

5. **Name the metric behind each chart by its `metric-definition` name**, with the grain, the time window and the comparison. ✅ `first_response_hours_p90` · daily · last 8 weeks · vs target 4h. A metric with no written definition is flagged `undefined: needs a spec before build`. That's a build blocker, not a detail for the BI developer to settle by guessing.

6. **Set the filters**, at most four global ones with their default values. Only offer a filter on a dimension each affected metric can be sliced by. A filter that fans out a metric (product category on order-level revenue) is left off with a note saying why.

7. **Set the refresh cadence and freshness SLA from the decision cadence.** A weekly decision needs a daily refresh at most; a live operations floor needs minutes. State the SLA (✅ *"data no older than 06:00 UTC each weekday"*), show a "data as of" timestamp on the dashboard, and say what happens when the data is stale: a visible banner, not a silently old chart. Don't pay for real-time on a weekly decision.

8. **Write the cut list.** Every metric or chart someone asked for that didn't make it, with the reason. Run the vanity test on each candidate: *"If this number doubled tomorrow, what would the audience do differently?"* No answer → cut. Usual cuts: all-time cumulative totals (they only go up), page views and sessions with no outcome attached, any metric the audience can't influence, and duplicates of the same question in another chart type.

9. **Sketch the layout** as a text grid: question 1's chart in the top row, supporting questions below, the detail table last. A reader from the audience should be able to answer question 1 from the top row without clicking anything.

10. **Emit with [`templates/dashboard-spec.md`](templates/dashboard-spec.md)** in one message: decision statement, questions with actions, chart table, filters, refresh and freshness, layout grid, cut list, and open questions (undefined metrics, data gaps, unconfirmed owners).

## Useful references in this skill

- [`reference.md`](reference.md) — the chart chooser with when-not-to rules, the vanity-metric test with common cuts, and refresh cadence by decision type
- [`templates/dashboard-spec.md`](templates/dashboard-spec.md) — the spec skeleton
- [`examples/support-staffing.md`](examples/support-staffing.md) — worked example: a support dashboard request with 14 asked-for metrics, cut to five questions

## Quality bar

- **A one-sentence decision statement** names who decides what, and how often.
- **At most seven questions, in priority order**, each with the action a bad answer triggers.
- **One chart per question, with a type and a reason.** No chart without a question.
- **Every chart names a metric by its defined name**, or flags it `undefined` as a build blocker.
- **Every number tile carries a comparison.**
- **Filters are four or fewer, have defaults, and never fan out a metric.**
- **Refresh cadence matches the decision cadence**, with a freshness SLA and a visible stale-data behaviour.
- **A cut list exists**, with a reason for each item, and vanity metrics are on it.
- **Nothing is invented.** Metrics, targets and data sources not given are marked `[assumption]` or `undefined`.

## When to use this skill

- ✅ Before a BI developer or analyst builds a new dashboard
- ✅ Rescuing a dashboard with too many charts that nobody opens
- ✅ "What should be on our exec / ops / team KPI dashboard?"
- ✅ Turning a list of requested metrics into a dashboard that serves one decision

## When NOT to use this skill

- ❌ Defining how one metric is calculated (formula, filters, timezone) — that's `metric-definition`
- ❌ Choosing which metric judges a feature, with targets and a decision rule — that's `success-metrics`
- ❌ Service health dashboards, SLOs and alerting — that's `observability-plan`
- ❌ A report on AI tool usage from telemetry logs — that's `ai-usage-report`

## Anti-patterns to avoid

- ❌ **The data-first dashboard.** Starting from "what tables do we have" and charting all of them. Start from the decision.
- ❌ **The 40-chart wall.** Built to look thorough, scanned by nobody, because no chart answers a question anyone asks.
- ❌ **Bare number tiles.** "Revenue: $1.2M" with no target or prior period can't tell anyone whether to act.
- ❌ **Pie charts with eight slices**, dual-axis charts and truncated bar axes. Each makes a comparison look different from what the data says.
- ❌ **Undefined metrics handed to the builder.** The BI developer picks a filter and a timezone, and the dashboard disagrees with finance on day one.
- ❌ **Real-time for a weekly meeting.** Paying for a live refresh that nobody looks at between Mondays.
- ❌ **No cut list.** Every requested chart creeps back in at review because nobody wrote down why it was left out.
- ❌ **Cumulative "growth" charts.** An all-time total only goes up, so it reads as success even while the business shrinks.
