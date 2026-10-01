---
name: tracker-brief-sync
description: Turn a brief or PRD (such as prd-draft output) into tracker-ready epics and issues — title, description, acceptance criteria, labels and a link back to the doc section — as a CSV for Jira, a mapped CSV for other importers, or gh commands for GitHub; and in reverse, report drift between the doc and the tracker (issues with no section, sections with no issue, issues for Won't-have requirements). Use when the user wants to load a PRD into Jira, Linear or GitHub, says "create tickets from this brief", or asks "does the tracker still match the PRD?".
---

# tracker-brief-sync

You keep a doc and a tracker saying the same thing. Going forward, you turn a brief or PRD into
epics and issues that a team can import, each linked back to the section it came from. Going
back, you compare the doc with the tracker and report where they disagree: work in the tracker
that the doc doesn't ask for, requirements nobody has an issue for, and issues for things the
doc rules out. A script checks the spec, writes the import file and computes the drift; you do
the mapping from doc to work, and the reading.

## How to respond

1. **Ask once for what's missing.** Work out which direction the user wants. Then:

   > Before I start, send these. Anything you skip, I'll use the default shown:
   > 1. **The doc:** the brief or PRD (a file, or pasted).
   > 2. **The tracker:** Jira, Linear or GitHub. *Default: Jira CSV.*
   > 3. **For drift:** the tracker export (CSV or JSON), or permission to fetch it via MCP.
   > 4. **Where the team reads the doc** (a wiki or repo URL), for the link on each issue.
   >    *Default: the file name.*
   > 5. **Labels** your team uses for this feature or area. *Default: one feature label.*

2. **Find the sections.** A PRD from `prd-draft` has requirement IDs (R1, R2…) and goals (G1…).
   A brief without IDs uses its `##` and `###` headings (run the script with `--headings`). If
   the doc has neither, ask the user to number the requirements first; don't match on wording.
   Rules are in [`reference.md`](reference.md).

3. **Forward: map the doc to items, and show the mapping before the spec.** One epic per goal
   that has requirements, one story per requirement. Won't-have requirements, non-goals and open
   questions become nothing, and you list them under "Not created". Acceptance criteria restate
   the requirement's observable behaviour as Given/When/Then; they add nothing the doc doesn't
   say. A requirement too large for one story goes to `user-story-splitter`, and you say so.

4. **Write the spec** in the shape of [`templates/issues-spec.json`](templates/issues-spec.json),
   then check and export it:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/brief_sync.py" export issues-spec.json --target jira --doc prd.md -o import.csv
   # Other IDEs (from the skill folder)
   python3 scripts/brief_sync.py export issues-spec.json --target jira --doc prd.md -o import.csv
   ```

   `--target csv` writes a plain mapped CSV; `--target github` writes a script of `gh` commands,
   because GitHub has no CSV import for issues. If the script lists problems (missing criteria,
   a parent that doesn't exist, a source not in the doc, a Won't-have source), fix the spec and
   rerun. It writes nothing until the spec is clean.

5. **Hand over with import steps.** Give the file, the mapping table, the import steps for the
   tracker from [`reference.md`](reference.md), the "Not created" list, and any open question
   that may add work. If the user has a tracker MCP tool and wants the issues created directly,
   create them from the checked spec, epics first, so each issue carries the same Source line.

6. **Reverse: run the drift check.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/brief_sync.py" drift --doc prd.md --export tracker-export.csv -o drift.md
   # Other IDEs (from the skill folder)
   python3 scripts/brief_sync.py drift --doc prd.md --export tracker-export.csv -o drift.md
   ```

7. **Read every flagged issue before reporting.** For each item of drift, say what happened
   (from the issue's description or status, not a guess), the two ways it could be resolved
   (change the tracker or change the doc), and who decides. Issues linked only by mentioning an
   ID need their Source line restored. Don't assume the tracker is the one that's wrong.

**Non-interactive runs** (subagent, CI, headless): with no doc, emit
`BLOCKED: need the brief or PRD to sync from` and stop. For drift with no export and no tracker
access, emit `BLOCKED: need the tracker export (CSV or JSON) or tracker access`. Otherwise use
the defaults above and list each assumption at the top.

## Useful references in this skill

- [`reference.md`](reference.md) — what counts as a section, the Source line, doc-to-item rules, the spec format, import steps per tracker, drift rules, field mapping for exports
- [`templates/issues-spec.json`](templates/issues-spec.json) — the spec the script reads
- [`scripts/brief_sync.py`](scripts/brief_sync.py) — `export` (check the spec, write the import file) and `drift` (stdlib, Python 3.9+)
- [`examples/guest-checkout-sync.md`](examples/guest-checkout-sync.md) — a PRD to a Jira CSV, then a drift check two weeks later, with the script's real output
- [`examples/prd-guest-checkout.md`](examples/prd-guest-checkout.md), [`examples/guest-checkout-spec.json`](examples/guest-checkout-spec.json), [`examples/tracker-after-two-weeks.csv`](examples/tracker-after-two-weeks.csv) — the example's inputs

## Quality bar

- **Every issue links back to its doc section** with a Source line the drift check can read.
- **Every story has acceptance criteria** that restate the doc's requirement, testably, without adding behaviour.
- **Won't-have requirements and non-goals produce no issues,** and are listed as not created.
- **The import file passes the spec check** before it's handed over, and comes with the import steps for the user's tracker.
- **Drift names each item and what happened,** from the issue's own text or status, with both ways to resolve it.
- **The doc and the tracker are treated as equals.** Drift is a disagreement, not proof the tracker is wrong.
- **Nothing is invented:** no requirements, numbers, owners or reasons that aren't in the doc or the export.

## When to use this skill

- ✅ A PRD or brief is agreed and the team needs it in Jira, Linear or GitHub
- ✅ Checking, mid-build, whether the tracker still matches the doc
- ✅ Before a review or launch, finding requirements nobody built and work nobody asked for
- ✅ After the doc changes, finding issues that point at removed or renumbered sections

## When NOT to use this skill

- ❌ Writing the PRD itself; use `prd-draft`, then bring its output here
- ❌ Slicing one epic into stories with a build order; use `user-story-splitter`
- ❌ Cleaning up an existing backlog (duplicates, stale items, ordering); use `backlog-triage`

## Anti-patterns to avoid

- ❌ **Creating an issue for a Won't-have requirement** "so it's not forgotten". The doc says it's out; the tracker should agree.
- ❌ **Acceptance criteria that add scope.** If the doc doesn't say "within 5 minutes", neither do the criteria.
- ❌ **Matching doc to tracker on title wording.** Titles get edited; the Source line and IDs don't.
- ❌ **Issues with no link back.** Without the Source line, next month's drift check can't tell where the issue came from.
- ❌ **Assuming the tracker is wrong.** A cancelled issue might mean the doc is out of date.
- ❌ **Pasting a GitHub "CSV"** and telling the user to import it. GitHub has no CSV issue import; use the gh script or the MCP.
- ❌ **Turning open questions into tickets** with guessed answers. Report them as unresolved.
