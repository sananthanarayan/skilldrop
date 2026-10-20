---
title: From an agreed PRD to a tracker that stays honest
summary: Load a PRD into Jira as epics and stories, triage the backlog it joins, write the weekly status from counted numbers, and catch where the tracker and the doc have drifted apart, with the trackers pack on one team's real files.
kind: tutorial
---

# From an agreed PRD to a tracker that stays honest

In about half an hour you'll take one agreed PRD into a tracker and keep the two honest for
the weeks the work lives there. You'll load it as issues, triage the backlog it joins, write
a weekly status from counted numbers, and find where the tracker and the doc have drifted.
Every number below comes from a script that read the export. None is the agent's estimate.

The example is one checkout team at Northwind, and the files ship with the skills. Every
output on this page is from running the pack's scripts on them.

## Install the pack

```bash
npx skilldrop-cli install --pack trackers
```

This adds `tracker-brief-sync`, `backlog-triage` and `team-status-report`, plus `core`. It
works from an export (CSV or JSON from Jira, Linear or GitHub Projects) or from a tracker's
MCP tool if you have one connected.

## Copy the team's files

```bash
mkdir northwind && cd northwind
S=~/.claude/skills
cp $S/tracker-brief-sync/examples/prd-guest-checkout.md $S/tracker-brief-sync/examples/tracker-after-two-weeks.csv .
cp $S/backlog-triage/examples/northwind-backlog.csv $S/team-status-report/examples/northwind-week-40.csv .
```

The PRD is "Checkout without an account". It has two goals and seven numbered requirements,
each tagged Must, Should or Won't have, and it must ship before the Black Friday code freeze.

## Load the PRD as issues

> Turn prd-guest-checkout.md into a Jira import.

The agent maps each goal to an epic and each requirement that needs work to a story, with
acceptance criteria and a link back to its section of the PRD. Then the script writes the
import file and checks it:

```text
wrote import.csv: 8 items (2 epics, 6 others)
```

Seven requirements, six stories: R7, saving a card for guest shoppers, is Won't have, so it
gets no issue. Review the mapping before you import. This is the one point where changing it
costs nothing.

## Triage the backlog the stories join

The new stories land in a backlog that already holds 20 items. Before refinement:

> Triage northwind-backlog.csv as of 1 October.

```text
| Check | Count |
|---|---:|
| Duplicate candidate pairs | 3 |
| No owner | 8 |
| No acceptance criteria | 11 |
| Stale (> 30 days) | 10 |
| Oversized | 3 |
| Priority conflicts | 11 |
```

One of the three duplicate pairs is the PRD itself, already in the backlog twice:

```text
| CHK-101 / CHK-104 | 0.80 | Guest checkout without creating an account / Allow guest checkout without an account |
```

One copy is Highest priority and the other Medium. Neither has an owner. The script compares
titles only. The agent reads both descriptions before it proposes a merge, and it writes
every proposed change to `changes.csv` for you to apply or reject. It doesn't edit the
tracker. Who owns the eight unowned items is your call.

## Write the weekly status from counts

At the end of week 40:

> Write this week's status from northwind-week-40.csv, 24 to 30 September.

The script counts first and suggests a RAG status from a rule it prints:

```text
## Suggested RAG: Red

Rule: Red if plan completion < 60% or >= 2 planned items blocked; Amber if completion < 85%, any planned item blocked, or a High-or-above planned item slipped; otherwise Green.
- Red: plan completion 50% is below 60%
- Amber: 1 planned item is blocked
- Amber: 3 High-or-above planned item(s) slipped: CHK-102, CHK-107, CHK-119
```

Five items shipped and four of the eight planned are done. A report that leads with "five
items shipped" reads green. The counted plan says the week was red, and the report says why
in the reader's terms. Tell the agent what the tracker can't show: that the PCI
questionnaire (CHK-107) is blocked on the security team's review, and who is chasing it.
The report names the blocker and its owner.

## Catch the drift after two weeks

Two weeks into the build, check the tracker against the PRD again:

> Check tracker-after-two-weeks.csv against prd-guest-checkout.md for drift.

```text
| Drift | Count |
|---|---:|
| Doc sections with no issue | 1 |
| Issues with no doc section | 1 |
| Issues pointing at a section the doc doesn't have | 1 |
| Issues for a Won't-have requirement | 1 |
```

Each line is a decision the team made without anyone deciding it:

- R3, offering the guest an account after they pay, has no issue, so it won't be built.
- CHK-210, Klarna for guest orders, is work no requirement asked for.
- CHK-211 points at R8, which the PRD doesn't have.
- CHK-209 builds saved cards for guests, which the PRD ruled out.

For each line the agent gives both ways to resolve it: change the tracker, or change the
doc. Which one is right is a product decision, so it's yours.

## What you have now

A tracker that traces to the PRD, a backlog with its duplicates and gaps named, a weekly
report whose colour follows a written rule, and a list of where the plan and the work have
parted. Rerun the drift check before each refinement and again before launch; it costs one
export.

Next: [Use the trackers pack](../how-to/packs/use-the-trackers-pack.md), or connect a tracker
directly with [Jira](../how-to/integrate-with-jira.md), [Linear](../how-to/integrate-with-linear.md)
or [GitHub Projects](../how-to/integrate-with-github-projects.md).
