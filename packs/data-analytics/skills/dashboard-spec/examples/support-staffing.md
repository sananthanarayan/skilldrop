# Worked example: support staffing dashboard

## Input

> Northwind's support team wants a dashboard. The regional support leads meet every Monday at 09:00 London time to move agents between queues for the week. They've asked for: total tickets all-time, tickets this week, tickets by queue, tickets by channel, first-response time, resolution time, CSAT, backlog, agents online, tickets per agent, top 10 tags, website help-centre page views, NPS, and a world map of customers. Defined metrics so far: `first_response_hours_p90` (with a 4-hour target per queue) and `open_backlog_tickets`. Data is in the Zendesk export in Snowflake, refreshed nightly.

No questions asked: the audience, the decision and its cadence, and the defined metrics are all in the prompt.

## Output

# Dashboard spec: Weekly queue staffing

**Audience:** regional support leads · **Owner:** support operations lead `[assumption]` · **Tool:** not chosen
**Decision:** Regional support leads decide every Monday which queues get more or fewer agents for the week.

## Questions, in priority order

| # | Question | If the answer is bad, they… |
|---|---|---|
| 1 | Which queues missed the 4-hour first-response target last week? | Move agents to those queues |
| 2 | Which queues have the biggest open backlog going into this week? | Add agents or schedule a backlog session |
| 3 | Is any queue's incoming volume trending up? | Plan staff ahead of the trend, not after it |
| 4 | How many tickets does an agent on each queue handle per week? | Size the move: how many agents fix the gap |
| 5 | Which queue and ticket combinations need a closer look? | Open the detail and assign follow-up |

## Charts

| # | Chart | Type | Why this type | Metric (defined name) | Grain · window · comparison |
|---|---|---|---|---|---|
| 1 | Which queues missed the 4h response target last week? | Sorted horizontal bar with a target line at 4h | Ranking against a threshold; the worst queue reads first | `first_response_hours_p90` | queue · last complete week · vs 4h target |
| 2 | Open backlog by queue, Monday 06:00 | Sorted horizontal bar | Ranking by size | `open_backlog_tickets` | queue · snapshot · vs same time last week |
| 3 | Incoming tickets per queue, last 8 weeks | Line chart, one line per queue (small multiples if more than five queues) | Change over time | `undefined: needs a spec before build` (incoming tickets: created time? merged tickets? spam?) | queue · weekly · last 8 weeks |
| 4 | Tickets handled per agent-week by queue | Number tiles, one per queue | Single current value per queue, used for arithmetic | `undefined: needs a spec before build` (what counts as handled; how agent-weeks are counted for part-timers) | queue · last complete week · vs 4-week average |
| 5 | Queue detail | Table, sorted by response time over target | Exact values for lookup | `first_response_hours_p90`, `open_backlog_tickets`, and the two undefined metrics | queue · last complete week |

## Filters

| Filter | Default | Applies to | Notes |
|---|---|---|---|
| Region | The viewer's region | All | |
| Week | Last complete week (Monday to Sunday, London time) | Charts 1, 4, 5 | |

Left off as filters: channel and tag. A ticket can carry several tags, so a tag filter would fan out the ticket counts; channel doesn't change a staffing decision made per queue.

## Refresh and freshness

- **Refresh:** nightly, matching the existing Snowflake load
- **Freshness SLA:** Sunday's data loaded by 06:00 London time on Monday, three hours before the meeting
- **When stale:** a red banner across the top naming the support operations lead
- **"Data as of" timestamp:** top right, on every view

## Layout

```
+-----------------------------------------------------------+
| Q1: Queues over 4h response target (sorted bar)           |
+-----------------------------+-----------------------------+
| Q2: Open backlog by queue   | Q3: Incoming tickets trend  |
+-----------------------------+-----------------------------+
| Q4: Tickets per agent-week tiles                          |
+-----------------------------------------------------------+
| Q5: Queue detail table                                    |
+-----------------------------------------------------------+
```

## Deliberately left off

| Requested item | Why it's cut |
|---|---|
| Total tickets all-time | Only goes up; changes no staffing decision |
| Tickets this week (single total) | Replaced by the per-queue trend in chart 3, which tells the leads where to move people |
| Tickets by channel | Staffing is by queue, not channel. Belongs on a channel-strategy dashboard. |
| Resolution time | Driven by product fixes and customer replies as much as staffing. Keep it for the monthly quality review. |
| CSAT, NPS | Lagging and not specific to a queue-staffing move this week. Monthly quality review. |
| Agents online | A live-floor number; the decision is weekly |
| Top 10 tags | Diagnostic, not a staffing input; tags also fan out counts |
| Help-centre page views | Activity with no action for this audience |
| World map of customers | Answers no question on the list |

## Open questions

- [ ] Incoming tickets needs a `metric-definition` spec (created time, merged and spam tickets). Owner: support operations lead.
- [ ] Tickets handled per agent-week needs a spec (what "handled" means, part-time agents). Owner: support operations lead.
- [ ] Confirm the dashboard owner.
