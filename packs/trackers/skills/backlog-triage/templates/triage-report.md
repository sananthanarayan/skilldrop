# Backlog triage template

Every count comes from the script output or a count you made from the export. Every verdict
(duplicate, priority change, position in the ordering) carries its reason.

```markdown
# Backlog triage: {team or project}, as of {YYYY-MM-DD}

{N} open items. {n} duplicate pairs, {n} with no owner, {n} with no acceptance criteria,
{n} stale (over {N} days), {n} oversized. {n} of {N} open items ({pct}%) are at {top priority}.
Checks skipped because the export lacked the column: {list, or "none"}.

## Duplicates (confirmed by reading both descriptions)

| Keep | Close | Why they're the same | Why this one survives |
|---|---|---|---|
| {key} | {key} | {the shared request, in one line} | {owner / criteria / evidence / recency} |

Rejected candidates (similar titles, different work): {key / key: why}, or "none".

## Proposed ordering (open, not yet started)

| # | Key | Title | Why here | Ready to pull? |
|---|---|---|---|---|
| 1 | {key} | {title} | {rule from the ordering method that placed it} | Yes / No: {what's missing} |

In progress and left where they are: {keys}.

## Priority conflicts to resolve

- **{conflict}.** {the facts from the export}. Proposal: {change}, unless {condition}.

## Change list

| Key | Change | Reason |
|---|---|---|
| {key(s)} | {close as duplicate of X / assign owner / add criteria / split with user-story-splitter / priority A → B (proposal) / confirm or close} | {fact from the export} |

## Questions before applying

1. {owner, date or priority the export can't answer}
```
