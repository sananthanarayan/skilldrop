# Trackers

For leads and PMs who run work in Jira, Linear or GitHub Projects: load a PRD into the tracker, triage the backlog, write the weekly status report, and check the tracker still matches the doc, all from an export or an MCP tool, with the numbers computed rather than estimated.

`/plugin install trackers@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Triage your backlog before the next refinement session

Paste this into Claude Code:

```text
Here's our backlog exported from Jira: ./backlog.csv. Refinement is Thursday. Find the duplicates, tell me what isn't ready to pull and why, and propose an order for what we take next. Anything without an update in 30 days counts as stale.
```

- **Before you start:** A CSV or JSON export of your backlog from Jira, Linear or GitHub, or a tracker MCP tool installed
- **Before you start:** Python 3.9 or later, for the counting scripts
- **How to tell it worked:** backlog-triage runs its script and reports exact counts (duplicate pairs, items with no owner or no acceptance criteria, stale and oversized items), names each duplicate pair with why they match, gives a reason for every position in the ordering, and ends with a change list you can apply.
- **If nothing happens:** If the counts say "n/a", the script didn't find a column: rerun it with --map, e.g. --map owner="Team Lead". If backlog-triage doesn't activate, ask for it by name ("use backlog-triage").

## Loops

- `ship-a-draft`

## Skills

- `backlog-triage`
- `brief-intake`
- `council-review`
- `doc-critique`
- `output-hygiene`
- `team-status-report`
- `tracker-brief-sync`

More: https://sananthanarayan.github.io/skilldrop/packs/trackers/
