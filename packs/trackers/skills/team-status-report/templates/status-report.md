# Team status report template

Every number comes from the script output or a stated count from the export. Facts the export
doesn't hold (what a blocker is, an expected date) come from the user and say so.

```markdown
# {Team} status: {period, e.g. 24–30 September 2026}

**Status: {Red | Amber | Green}.** Rule: {the condition that set it, with the number}.
{One sentence: planned-and-done of planned (pct), and what that means.}
{If no plan: "There's no plan to measure against this week, so this status reflects blockers only."}

## Shipped ({n})

- {key} {title, in plain words} ({owner}), {date}{. Unplanned: why it came in, if known}

## Slipped against plan ({n} of {planned} due)

| Item | Owner | Where it is | Priority |
|---|---|---|---|
| {key} {title} | {owner or "No owner"} | {status, or "Blocked by X"} | {priority} |

{New dates only if the owners gave them.}

## Blocked ({n})

| Item | Owner | Blocked by | Expected |
|---|---|---|---|
| {key} {title} | {owner} | {blocker key, and what it is if the user said} | {date and who said so, or "No date"} |

## In progress ({n})

{keys and titles, one line}

## Risks

- **{what could go wrong}.** {the fact behind it} · {what it threatens, by when}

## Asks

1. **{who}:** {what}, by {when}. {which item it unblocks}
```
