# backlog-triage reference

## Getting the export

The script reads CSV, TSV, JSON or JSONL. Pick whichever your tracker gives you most easily.

| Tracker | Export route | Notes |
|---|---|---|
| Jira | Issue search (filter the backlog with JQL, e.g. `project = CHK AND statusCategory != Done`) → Export → CSV (all fields) | Repeated columns such as `Labels, Labels` are joined. Story points usually appear as `Custom field (Story Points)` |
| Linear | Workspace settings → import/export → export CSV, or copy issues through the Linear MCP | Numeric priority 0–4 is understood (1 = Urgent … 4 = Low, 0 = none) |
| GitHub Issues | `gh issue list --state open --limit 500 --json number,title,body,state,assignees,labels,createdAt,updatedAt > issues.json` | Gives dates, so staleness works. No priority or estimate unless you use labels |
| GitHub Projects | `gh project item-list <number> --owner <org> --format json > items.json`, or the view's export to CSV if your view offers it | Custom fields (Status, Priority, Size) come through by name. Item lists may not carry an updated date; join with `gh issue list` if you need staleness |
| Any tracker via MCP | Ask the agent to fetch the open issues with the tracker's MCP tool and save the result as JSON | Objects nested under `fields` (Jira REST) or `content` (GitHub Projects) are flattened |

## Field mapping

The script looks for these column names, case-insensitively, and uses the first it finds.
Override any of them with `--map field="Your Column"`.

| Field | Jira CSV | Linear | GitHub Issues / Projects | Used for |
|---|---|---|---|---|
| key | Issue key | ID / identifier | number | Naming items in findings |
| title | Summary | Title | title | Duplicate detection (required) |
| description | Description | Description | body | Acceptance-criteria check |
| acceptance | Custom field (Acceptance Criteria) | (none) | (none) | Acceptance-criteria check, if your Jira has the field |
| status | Status | Status / state | state / Status | Skipping done items |
| owner | Assignee | Assignee | assignees | No-owner check |
| priority | Priority | Priority | Priority (Projects field) or labels | Priority conflicts |
| estimate | Custom field (Story Points), Story point estimate | Estimate | Size / Estimate (Projects field) | Oversized check |
| created | Created | Created / createdAt | createdAt | Fallback when there's no updated date |
| updated | Updated | Updated / updatedAt | updatedAt | Staleness |
| resolved | Resolved | Completed / completedAt | closedAt | Skipping done items |
| labels | Labels | Labels | labels | Shown in context |

A missing column turns its check off, and the report says which checks were skipped. A
missing title column stops the run.

## How each check works

| Check | Rule | Default |
|---|---|---|
| Open | Status not in the done set (Done, Closed, Resolved, Completed, Canceled, Duplicate, Won't Do, Released, Shipped) and no resolved date | — |
| Duplicate candidate | `difflib.SequenceMatcher` ratio on titles, lower-cased, punctuation and common stopwords removed | `--similarity 0.75` |
| No owner | Owner empty, "Unassigned" or "None" | — |
| No acceptance criteria | Description has none of: "acceptance criteria", "definition of done", "AC:", a Given/When/Then line, a `- [ ]` checklist; and the acceptance column (if any) is empty | — |
| Stale | Days from last update (or created, if no update) to `--as-of` | `--stale-days 30` |
| Oversized | Numeric estimate above the limit, or size XL / XXL | `--max-estimate 8` |
| Priority conflict | Top-two priority but unowned or stale; a duplicate pair at different priorities; more than the threshold share of open items at the top priority | `--inflation-pct 25` |

### Priority ranks

| Rank | Values recognised |
|---|---|
| 0 (top) | Highest, Blocker, Urgent, Critical, P0, Linear `1` |
| 1 | High, Major, P1, Linear `2` |
| 2 | Medium, Normal, P2, Linear `3` |
| 3 | Low, Minor, P3, Linear `4` |
| 4 | Lowest, Trivial, P4 |
| none | No priority, None, Linear `0` |

Anything else is listed as "not recognised" and left unranked. Tell the user, and map it
yourself when you write the ordering.

## Limits of the mechanical checks

- **Title similarity misses reworded duplicates** ("Pay later with Klarna" vs "BNPL option") and
  flags look-alikes that differ ("Export invoices as PDF" vs "Import invoices from PDF"). Read
  both descriptions before calling a pair a duplicate. Look for reworded duplicates yourself
  among items with the same label or component.
- **The acceptance-criteria check is a text search.** "We need AC" matches nothing; "AC: TBD"
  matches but is empty. Spot-check the items you're about to put at the top.
- **Staleness measures tracker activity, not relevance.** A Lowest item untouched for a year is a
  close candidate; a High item untouched for a year is a priority question.
- **Pair-wise comparison is O(n²).** Up to a few thousand items is fine. For larger exports,
  filter to one project or component first.

## Ordering method

Order open, not-started items by these, in turn. State which one placed each item.

1. **A fixed external date** (regulator, contract, event). Ask for the date if the description
   only hints at one; never assume it.
2. **Users currently harmed** (a bug with reports, a payment or access failure), more if the
   description gives a count.
3. **Ready to pull:** owner, acceptance criteria, and size within the limit. An item that isn't
   ready can't be first, however valuable. Put its readiness work at the top instead.
4. **Stated value over size.** Use the value the item itself claims; don't invent a business case.
5. **Everything else** keeps its current relative order.

In-progress items are not reordered. Report them separately.

## Change list format

The `--changes` CSV has `key, action, field, proposed_value, reason`. Actions:

| action | What applying it means |
|---|---|
| confirm-duplicate | Read both; close the weaker one as a duplicate and link it to the survivor |
| assign-owner | Set the assignee (the user names who) |
| add-acceptance-criteria | Write criteria, or hand to `user-story-splitter` if the item is also large |
| confirm-or-close | Ask the reporter whether it's still wanted; close if no answer by a date |
| split | Hand to `user-story-splitter` before it's scheduled |

The script's list is mechanical. The final change list you give the user removes rows your
judgment overrode (for example, both items of a pair you decided aren't duplicates) and adds the
priority changes you proposed.
