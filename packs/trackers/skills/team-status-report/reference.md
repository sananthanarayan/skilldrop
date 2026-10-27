# team-status-report reference

## Getting the data

Export every issue touched in the period, plus everything that was due in it. Done items need
a resolved date, or "shipped" can't be counted properly.

| Tracker | Route | Columns to include |
|---|---|---|
| Jira | Issue search, e.g. `project = CHK AND (updated >= -14d OR duedate <= endOfWeek())` → Export → CSV (all fields) | Resolved, Due date, Sprint, `Inward issue link (Blocks)` for blockers |
| Linear | Export CSV from workspace settings, or fetch the team's issues for the cycle through the Linear MCP | Completed, Due date, Cycle |
| GitHub | `gh issue list --state all --search "updated:>=2026-09-24" --limit 500 --json number,title,state,assignees,labels,closedAt,updatedAt,milestone > issues.json` | closedAt; the milestone works as the plan with `--sprint` |
| GitHub Projects | `gh project item-list <number> --owner <org> --format json`, or the view's CSV export if your view offers it | Status, Iteration, any date field you use as a due date |
| Any tracker via MCP | Ask the agent to fetch the issues and save them as JSON | Same fields as above, whatever they're called |

## Field mapping

Matched case-insensitively; first match wins. Override with `--map field="Your Column"`.

| Field | Jira CSV | Linear | GitHub | Used for |
|---|---|---|---|---|
| key | Issue key | ID / identifier | number | Naming items |
| title | Summary | Title | title | Naming items (required) |
| status | Status | Status / state | state / Status | Bucketing (required) |
| owner | Assignee | Assignee | assignees | Blocked owner, WIP by owner, unowned risks |
| priority | Priority | Priority (names or 0–4) | Priority field or labels | Slipped High items, risk candidates |
| resolved | Resolved | Completed / completedAt | closedAt | Shipped in period |
| updated | Updated | Updated / updatedAt | updatedAt | Fallback for shipped; last update on blocked items |
| due | Due date | Due date | a date field | Default plan |
| sprint | Sprint | Cycle | milestone / Iteration | Plan with `--sprint` |
| blocker | Blocked by, `Inward issue link (Blocks)`, `Custom field (Flagged)` | Blocked by | (label `blocked` + a note) | Blocker shown on blocked items |
| labels | Labels | Labels | labels | A `blocked` label marks an item blocked |

## Buckets

| Bucket | Rule |
|---|---|
| Done | Status is Done, Closed, Resolved, Complete(d), Released, Shipped or Merged |
| Dropped | Canceled, Duplicate, Won't Do, Won't Fix, Obsolete. Not counted as shipped, and removed from the plan |
| Blocked | Status Blocked, On Hold, Impeded or Waiting; or a `blocked` label; or a value in the blocker column |
| Not started | To Do, Backlog, Open, New, Triage, Ready, Selected for Development, Planned, Unstarted |
| In progress | Anything else (In Progress, In Review, QA, …) |
| Shipped in period | Done, with a resolved date inside `--from`..`--to` |

If your workflow has other status names, check the script's bucket counts against the board
before you trust them, and tell the user which statuses fell into "in progress" by default.

## The plan

"Slipped" only means something against a plan. The plan is the set of items that were meant
to be done by the end of the period:

| Source | Flag | Use when |
|---|---|---|
| A list of keys | `--plan-file plan.txt` | You have the sprint commitment or the list from last week's report |
| A sprint, cycle or milestone | `--sprint "CHK Sprint 14"` | The sprint ends inside the reporting period |
| Due dates | (default) | The team sets due dates; items due inside the period are the plan |

Slipped = planned and not done by the period end. Plan completion = planned-and-done ÷ planned.
Shipped work that wasn't in the plan is reported separately, never added to the completion
rate. With no plan source the script says so, and the report must say "no plan to measure
against" rather than implying the team is on track.

## The RAG rule

The script suggests a RAG status and prints every condition that fired:

| Colour | Default condition | Flag |
|---|---|---|
| Red | Plan completion below 60% | `--red-below` |
| Red | 2 or more planned items blocked | `--red-blocked` |
| Amber | Plan completion below 85% | `--amber-below` |
| Amber | Any planned item blocked | — |
| Amber | Any High-or-above planned item slipped | — |
| Green | None of the above | — |

The highest colour that fired wins. If the team already has a RAG rule, set the thresholds to
match it and say so. If the user wants to overrule the computed colour, report both: "Computed
Red (completion 50%); reported Amber because …". Never change the colour without saying why.

## What counts as a risk

The script lists mechanical candidates: planned items that are blocked, planned items with no
owner, and top-priority items not yet started. Add risks from the user's context (a fixed date,
a dependency on another team), each with what it threatens and by when. A risk without a
consequence is just a worry.

## What counts as an ask

An ask names who, what, and by when: "Platform team: a date for API-412 by Friday". Each ask
should unblock a blocked item, staff an unowned one, or settle a priority. Without an owner and
a date it's a wish.
