# dashboard-spec reference

## Chart chooser

| The question asks… | Use | Don't use | Notes |
|---|---|---|---|
| How has it changed over time? | Line chart | Bar chart with 30+ bars, area chart for several overlapping series | Mark the target as a reference line. Label the last point. |
| Which category is highest or lowest? | Horizontal bar, sorted | Pie, unsorted bars | Bars start at zero; a truncated axis exaggerates differences. |
| Is the current value on target? | Number tile with comparison | Gauge, speedometer | Always show the comparison: vs target, vs last period, or both. |
| How is a whole split, with three parts or fewer? | Stacked bar (100%), or a pie for two or three parts | Pie with more than three slices | People compare lengths more accurately than angles. |
| How are values spread out? | Histogram, box plot | Average alone | An average hides the tail; show the spread or a percentile. |
| Do two measures move together? | Scatter plot | Dual-axis line chart | Dual axes let the chart's author pick the apparent correlation. |
| What is the exact value for a given item? | Table, sorted, with conditional formatting on the key column | A chart someone has to hover over | Put the table last; it's for lookup, not for the headline. |
| Where did the change come from? | Bar of contributions (waterfall) | Two pies side by side | Use when the question is "why did it move". |

General rules: one question per chart; the title states the question or the answer (✅ *"Queue B is 2.1h over target"* or *"Which queue is furthest over target?"*), not the metric name alone; no 3D; colour carries meaning (over target, under target) and is never the only cue.

## The vanity test

Ask of every candidate metric: **"If this number doubled tomorrow, what would the audience do differently?"** If nobody can name an action, cut it.

Common cuts:

- **All-time cumulative totals** (total registered users, lifetime orders). They only go up, so they read as success regardless of what's happening now.
- **Activity without outcome** (page views, sessions, logins, emails sent). Keep only if paired with an outcome the audience owns.
- **Metrics the audience can't move.** A regional lead can't act on global marketing spend.
- **The same question twice**, in a different chart type or a slightly different metric.
- **"Nice to know" context** that nobody checks. Put it on a linked detail page, not the main view.

## Refresh cadence by decision type

| Decision cadence | Refresh | Freshness SLA example |
|---|---|---|
| Live operations (support floor, incident) | Minutes | Data no older than 5 minutes |
| Daily stand-up or daily ops | Daily, before the meeting | Refreshed by 07:00 in the team's timezone |
| Weekly review | Daily | Refreshed by 06:00 on the review day |
| Monthly or board reporting | Daily, with the month locked after close | Month figures final on the agreed close day |

Every dashboard shows a "data as of" timestamp. When the freshness SLA is missed, the dashboard shows a visible stale-data banner and names the owner to contact. A chart that is silently a day old gets acted on as if it were current.

## Filter rules

- Four or fewer global filters, each with a default. More than that and every viewer sees a different dashboard.
- A filter applies only where every affected metric can be sliced by that dimension (see each metric's allowed dimensions).
- The date filter's default matches the decision: "last complete week" for a weekly review, not "last 7 days" ending mid-day today.
