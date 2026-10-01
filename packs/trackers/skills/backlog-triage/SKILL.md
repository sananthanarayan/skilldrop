---
name: backlog-triage
description: Triage a whole backlog export from Jira, Linear or GitHub Projects (CSV, JSON or an MCP tool) — duplicate and near-duplicate pairs with the reason, items missing acceptance criteria or an owner, stale items, oversized items to split, priority conflicts, and a proposed ordering with a reason per item — ending in a change list the user can apply. A stdlib script computes the mechanical checks. Use when the user wants to clean up, groom or refine a backlog, find duplicate tickets, or says "triage our backlog", "what should we pull next?".
---

# backlog-triage

You take a whole backlog, not one ticket, and turn it into a short list of changes someone can
apply before refinement: which items are duplicates, which can't be pulled yet and why, which
have gone stale, which are too big, where the priorities contradict each other, and what order
to work in. A script does the counting so the numbers are exact; you do the reading and the
judgment. Works from a CSV or JSON export, or from issues fetched through a Jira, Linear or
GitHub MCP tool.

## How to respond

1. **Ask once for what's missing.** You need the export (a file path, or permission to fetch the
   open issues through the tracker's MCP tool). Offer defaults so the user can reply "go":

   > Before I triage, send these. Anything you skip, I'll use the default shown:
   > 1. **The export:** a CSV or JSON file, or say which project to fetch via MCP.
   > 2. **Stale after:** *Default: 30 days without an update.*
   > 3. **Too big to schedule:** *Default: an estimate above 8 points, or size XL.*
   > 4. **Anything with a fixed date** (a contract, a regulator, an event)?
   > 5. **Who decides priority**, so I know whom the questions go to?

   Export routes for each tracker are in [`reference.md`](reference.md).

2. **Run the script on the export.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/triage_backlog.py" backlog.csv --as-of 2026-10-01 -o triage-findings.md --changes changes.csv
   # Other IDEs (from the skill folder)
   python3 scripts/triage_backlog.py backlog.csv --as-of 2026-10-01 -o triage-findings.md --changes changes.csv
   ```

   It prints which columns it mapped and which checks it skipped for lack of a column. If it
   mapped the wrong column, rerun with `--map owner="Team Lead"`. Tracker-by-tracker column names
   are in the field-mapping table in [`reference.md`](reference.md).

3. **Confirm each duplicate candidate by reading both descriptions.** The script matches titles
   only. For each pair, say whether it's the same work and why, and which item survives (the one
   with the owner, the acceptance criteria, the evidence, or the most recent activity). Reject
   look-alikes that differ ("Export invoices" vs "Import invoices"). Then look for reworded
   duplicates the script can't see, among items that share a label or component.

4. **Turn missing fields into readiness.** An item with no owner or no acceptance criteria isn't
   ready to pull, whatever its priority. Don't write the criteria yourself unless asked; flag the
   gap. Items over the size limit go to `user-story-splitter` before they're scheduled.

5. **Treat staleness by priority.** A low-priority item untouched for months is a close
   candidate. A high-priority item untouched for months is a priority question for the user, not
   a close.

6. **Resolve priority conflicts as proposals.** Use the script's mechanical conflicts (top
   priority but unowned or stale, duplicates at different priorities, too much at the top) and
   add any you see from reading. Propose a change with its reason. Never change a priority
   silently.

7. **Propose an ordering** for open, not-started items using the ordering method in
   [`reference.md`](reference.md): fixed external date, then users currently harmed, then
   ready-to-pull, then stated value against size. Give each position its reason and say whether
   the item is ready. Leave in-progress items where they are.

8. **Emit with [`templates/triage-report.md`](templates/triage-report.md)**: summary counts,
   confirmed duplicates, the ordering, priority conflicts, the change list, and the questions only
   the user can answer (owners, dates, who wants a stale item). The counts are the script's; if
   you counted anything yourself, say how.

**Non-interactive runs** (subagent, CI, headless): with no export and no MCP access, emit
`BLOCKED: need the backlog export (CSV or JSON) or tracker access` and stop. With an export, use
the defaults above and list each assumption at the top of the report.

## Useful references in this skill

- [`reference.md`](reference.md) — export routes, the field-mapping table for Jira, Linear and GitHub, how each check works, priority ranks, the ordering method, the change-list actions
- [`templates/triage-report.md`](templates/triage-report.md) — the report skeleton
- [`scripts/triage_backlog.py`](scripts/triage_backlog.py) — the mechanical checks (stdlib, Python 3.9+)
- [`examples/northwind-checkout-triage.md`](examples/northwind-checkout-triage.md) — a 20-issue Jira export, the script's real output, and the finished triage
- [`examples/northwind-backlog.csv`](examples/northwind-backlog.csv) — the sample export used in the example

## Quality bar

- **Numbers come from the data.** Counts, ages and estimates are the script's output or a stated count from the export, never an estimate.
- **Every duplicate names the pair and why.** Which two keys, what makes them the same work, and which one survives.
- **Readiness is explicit.** Each item in the ordering says whether it can be pulled today, and if not, what's missing.
- **Each position in the ordering has a reason** tied to the ordering method, not "feels important".
- **Priority changes are proposals,** each with the facts behind it, addressed to whoever owns priority.
- **The change list can be applied as written:** key, change, reason, one row per action.
- **Nothing is invented.** No owner, date, estimate or customer count that isn't in the export or the user's message.

## When to use this skill

- ✅ Before backlog refinement or sprint planning, to clean a backlog of dozens or hundreds of items
- ✅ Finding duplicate and near-duplicate tickets across a project
- ✅ "What should we pull next?" with a reason for each pick
- ✅ Taking over a backlog from another team and finding what's stale or unowned

## When NOT to use this skill

- ❌ One bug report to turn into a ticket; use `bug-triage`
- ❌ Splitting one epic or large item into stories; use `user-story-splitter` (this skill hands oversized items to it)
- ❌ A weekly status update for stakeholders; use `team-status-report`
- ❌ Creating issues from a PRD, or checking the tracker against the doc; use `tracker-brief-sync`

## Anti-patterns to avoid

- ❌ **Closing on title similarity alone.** "Export invoices as PDF" and "Import invoices from PDF" score high and are different work.
- ❌ **Estimating counts.** "About a third of the backlog is stale" when the script gave you the exact number.
- ❌ **Putting an unready item first** because it's marked Highest. Put its readiness work first instead.
- ❌ **Closing high-priority stale items.** That's a question for the priority owner, not a tidy-up.
- ❌ **Writing acceptance criteria nobody asked for** and presenting them as the team's.
- ❌ **A ranking with no reasons.** If you can't say why item 3 is above item 4, it isn't an ordering.
- ❌ **Silently re-prioritising.** Every priority change is a proposal in the change list.
