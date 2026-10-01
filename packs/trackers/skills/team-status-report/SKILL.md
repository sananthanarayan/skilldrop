---
name: team-status-report
description: Write a weekly team status report from tracker data (Jira, Linear or GitHub Projects, via CSV, JSON or an MCP tool) — shipped, in progress, blocked with the blocker and owner, slipped against plan, risks and asks — with every number computed from the data by a stdlib script, never estimated, and a RAG status that states the rule that set it. Use when the user wants a weekly status update, sprint report or stakeholder update from the tracker, or says "write this week's status report", "are we on track?".
---

# team-status-report

You turn a tracker export into the status report a manager or steering group reads in two
minutes: what shipped, what's moving, what's stuck and on whom, what slipped against the plan,
what could go wrong next, and what you need from them. A script computes every count, so the
numbers are exact and the same next week. The RAG colour comes from a stated rule, not a mood.
Facts the tracker doesn't hold, such as what a blocker actually is, come from the user and are
marked as theirs.

## How to respond

1. **Ask once for what's missing.** Take what's been given and offer defaults:

   > Before I write the report, send these. Anything you skip, I'll use the default shown:
   > 1. **The export:** a CSV or JSON file, or which project or team to fetch via MCP.
   > 2. **The period:** *Default: the last 7 days, ending yesterday.*
   > 3. **The plan:** a list of keys, a sprint or cycle name, or *default: items due in the period.*
   > 4. **Your RAG rule,** if the team has one. *Default: Red below 60% of plan or 2+ planned
   >    items blocked; Amber below 85%, any planned item blocked, or a High item slipped.*
   > 5. **Who reads it,** and anything the tracker doesn't show: what each blocker is, dates
   >    other teams have promised, fixed deadlines.

   Export routes per tracker are in [`reference.md`](reference.md).

2. **Run the script for the period.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/status_counts.py" export.csv --from 2026-09-24 --to 2026-09-30 -o status-numbers.md --json status-numbers.json
   # Other IDEs (from the skill folder)
   python3 scripts/status_counts.py export.csv --from 2026-09-24 --to 2026-09-30 -o status-numbers.md --json status-numbers.json
   ```

   Add `--plan-file plan.txt` or `--sprint "Sprint 14"` to set the plan, and `--red-below`,
   `--amber-below` or `--red-blocked` to match the team's RAG rule. If a column was mapped wrong,
   rerun with `--map blocker="Blocked reason"`. The field-mapping table is in
   [`reference.md`](reference.md).

3. **Check the buckets before you write.** Read the "Columns used" line and the data notes. If
   a status your team uses fell into "in progress" by default, or done items have no resolved
   date, fix the mapping or tell the user what that does to the numbers.

4. **Lead with the RAG and its rule.** State the colour, the condition that set it, and the
   number: "Red. Rule: plan completion below 60%. We finished 4 of 8 items due (50%)." If there's
   no plan, say the status reflects blockers only. If the user overrules the computed colour,
   show both and the reason.

5. **Write shipped, slipped, blocked and in progress from the script's tables.** Rewrite titles
   into plain words for the audience, but keep the keys. Each blocked item names its blocker and
   its owner. If the blocker isn't recorded, write "blocker not recorded" and ask; don't guess.
   Unplanned work that shipped is listed, and isn't added to the plan completion.

6. **Add risks and asks.** Start from the script's risk candidates and add the user's context.
   Each risk says what it threatens and by when. Each ask names who, what and by when, and which
   item it unblocks.

7. **Emit with [`templates/status-report.md`](templates/status-report.md).** Keep it to one
   screen. Keep keys so readers can click through. Say what the report can't tell them (no
   velocity without estimates, no new dates unless owners gave them).

**Non-interactive runs** (subagent, CI, headless): with no export and no tracker access, emit
`BLOCKED: need the tracker export (CSV or JSON) or tracker access, and the reporting period`
and stop. With an export, use the defaults above, list each assumption at the top, and write
"blocker not recorded" wherever the export lacks one.

## Useful references in this skill

- [`reference.md`](reference.md) — export routes, the field-mapping table for Jira, Linear and GitHub, bucket rules, plan sources, the RAG rule, what makes a risk and an ask
- [`templates/status-report.md`](templates/status-report.md) — the report skeleton
- [`scripts/status_counts.py`](scripts/status_counts.py) — the counts, plan vs actual and suggested RAG (stdlib, Python 3.9+)
- [`examples/northwind-weekly-status.md`](examples/northwind-weekly-status.md) — a 15-issue Jira export, the script's real output, and the finished report
- [`examples/northwind-week-40.csv`](examples/northwind-week-40.csv) — the sample export used in the example

## Quality bar

- **Every number is computed from the data,** by the script or a stated count. No "about", no "roughly half", no velocity the data can't support.
- **The RAG names its rule** and the number that triggered it. Green with no plan says so.
- **Blocked items name the blocker and the owner,** or say "not recorded".
- **Slipped is measured against a stated plan,** and unplanned work is shown separately, not folded into completion.
- **Facts from outside the tracker are attributed:** "3 Oct (security team, per user)".
- **Each ask has a who, a what and a when,** and points at the item it unblocks.
- **Nothing is invented:** no dates, causes, owners or blockers the export and the user didn't give.

## When to use this skill

- ✅ A weekly or fortnightly status update for a manager, a steering group or a client
- ✅ An end-of-sprint or end-of-cycle report against what was committed
- ✅ "Are we on track?" answered with numbers and a stated rule
- ✅ The same report every week, comparable because the counting doesn't change

## When NOT to use this skill

- ❌ Condensing a long document into a one-page summary for executives; use `exec-summary`
- ❌ Cleaning up the backlog itself (duplicates, stale items, ordering); use `backlog-triage`
- ❌ Recording a decision and its rationale; use `decision-log`

## Anti-patterns to avoid

- ❌ **"We're about 70% done."** Give planned-and-done of planned, from the script.
- ❌ **Amber by feel.** If no rule fired Amber, it isn't Amber. If the user wants Amber anyway, show the computed colour too.
- ❌ **"Blocked on infra."** Name the blocking item, the owner on our side, and what's expected when.
- ❌ **Counting unplanned work toward the plan** to make completion look better.
- ❌ **Inventing new dates for slipped items.** Leave them out until owners give them.
- ❌ **A status wall.** Twenty in-progress items listed in full. Count them; list the ones that matter.
- ❌ **Per-person scorecards.** WIP by owner is for spotting overload, not ranking people.
