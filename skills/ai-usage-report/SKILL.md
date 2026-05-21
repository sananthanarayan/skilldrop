---
name: ai-usage-report
description: Generate a per-user or team-level report on how AI tools are being used — volume, breadth, and effectiveness signals (e.g. whether AI outputs landed in shipped artifacts vs were generated and discarded). Consumes usage-event logs exported from an MCP server or other telemetry source. Use when a manager or team lead needs to understand AI adoption beyond raw counts — including spotting "AI theater" where people invoke AI to claim usage but don't act on the outputs.
---

# ai-usage-report

You help the user turn a raw AI-usage log into a readable, useful report — one that distinguishes "people doing real work with AI" from "people pressing the button to be seen pressing the button."

This skill **consumes** telemetry that someone else collected (an MCP server, an IDE telemetry pipeline, a manual CSV export). It does **not** collect the data itself. Your job is to:

1. Take the input file from the user.
2. Run the report script to compute aggregates and effectiveness signals.
3. Wrap the output with a short executive narrative tailored to the requesting audience.

## How to respond

1. **Confirm three inputs** before generating anything:

   - **Input file.** A CSV or JSONL of usage events. Schema lives in [`templates/usage-event-schema.md`](templates/usage-event-schema.md). If the user's file columns don't match the schema, *map the columns with them* before running — don't guess at field names.

   - **Reporting period.** `week`, `month`, or explicit `--from <date> --to <date>`. If the user gives a fuzzy period ("recently"), pick the last 7 calendar days and call out your choice.

   - **View.** Exactly one of:
     - `per-user` — named breakdown, manager view, includes effectiveness scores
     - `team-rollup` — aggregate-only, no individual names, safe for staff/exec audiences
     - `effectiveness` — focused on AI-theater flags and outputs-not-consumed signals

     If the user hasn't picked a view, **ask**. Defaults aren't safe here — the wrong view in the wrong audience's hands creates a workplace problem.

2. **Call out what the data does NOT support before running.** If the events have no `output_consumed` field, you cannot compute effectiveness — say so. If `session_id` is missing, you cannot compute breadth-per-session. The report should not invent numbers it doesn't have evidence for. Read the input's header (CSV) or first object (JSONL) and list which optional fields are present.

3. **Run the build script.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/build_report.py" /path/to/events.csv \
     --view per-user --period week --out ./out/ai-usage-week.md

   # Other IDEs (from the skill folder)
   cd path/to/ai-usage-report && python3 scripts/build_report.py /path/to/events.csv \
     --view per-user --period week --out ./out/ai-usage-week.md
   ```

   The script writes a markdown file using the matching template in `templates/`. Read it before handing back — sanity-check that the numbers reconcile with the input row counts.

4. **Add a 3-sentence handoff** above the report when delivering:
   - **One sentence on volume** — total invocations, distinct users, period covered.
   - **One sentence on what the data does and doesn't show** — flag missing signals explicitly.
   - **One sentence on the most actionable pattern** — usually either "X users haven't engaged" or "Y% of outputs were generated but never consumed."

   Then the report itself.

5. **Do not make a recommendation about specific named individuals** in the handoff. The report shows what it shows; turning patterns into HR-style judgments is the manager's call, not the skill's.

## Useful references in this skill

- [`templates/usage-event-schema.md`](templates/usage-event-schema.md) — the input event schema (required vs optional fields, graceful-degradation rules)
- [`templates/report-per-user.md`](templates/report-per-user.md) — per-user named-report layout
- [`templates/report-team-rollup.md`](templates/report-team-rollup.md) — aggregate team-level layout
- [`examples/weekly-engineering-team.md`](examples/weekly-engineering-team.md) — worked example: stub events → both report views
- [`scripts/build_report.py`](scripts/build_report.py) — the generator (stdlib only)

## Effectiveness signals (what "performative vs effective" actually means here)

The skill has **no magic classifier**. It exposes a set of signals the user interprets. Each signal is a column or counter in the report.

| Signal | What it means | When it's reliable |
|---|---|---|
| **`output_consumed` rate** | % of AI invocations whose output landed in a shipped artifact (commit, PR, doc) | Only if telemetry tracks downstream consumption. If absent, this column is omitted, not faked. |
| **Single-shot rate** | % of sessions with exactly one invocation and no follow-up | High single-shot + low effectiveness = a starting place to ask about engagement |
| **Breadth** | Number of distinct tools/skills the user invoked | Low breadth + high volume = one-trick usage pattern |
| **Session depth** | Avg invocations per session | High depth often correlates with iterative, engaged use |
| **Output-to-shipped lag** | Median hours between AI invocation and artifact ship | Only meaningful if downstream consumption is tracked |
| **Discard rate** | % of outputs explicitly rejected (IDE-level signal) | Requires IDE instrumentation; many sources lack this |

**None of these signals is a verdict.** A high single-shot rate could mean theater, or it could mean the user solved their problem in one prompt. Low breadth could mean focused expertise. The report's job is to surface patterns; the manager's job is to interpret them.

## Quality bar

- **Numbers are computed from the input, not estimated.** If the script cannot compute a metric (missing field), the column is omitted with a note. Never fill with `~` or `est.` placeholders.
- **Per-user reports include only users present in the input.** Don't infer missing users from elsewhere.
- **The "AI theater" framing lives in section headers, not in per-user judgments.** Say "Single-shot rate: 87%" — never "Alice is doing AI theater."
- **Privacy posture matches the view.** `per-user` names individuals; `team-rollup` never names anyone, even in passing.
- **Recommendations target patterns, not people.** "Consider a deeper-engagement workshop for the team" — never "Coach Alice to engage more deeply."
- **Period is explicit on the report header.** Every report shows the dates it covers.
- **Sample size is honored.** If `n_users < 5` in a team-rollup, the report is no longer anonymous — refuse to generate the team-rollup view and tell the user why.

## When to use this skill

- ✅ A manager has a CSV/JSONL of AI usage events and wants a weekly/monthly read.
- ✅ A team lead wants to spot adoption gaps without naming individuals.
- ✅ An exec needs an AI-adoption rollup that doesn't read like a control panel.
- ✅ Building a baseline before/after rolling out a new AI tool or training.

## When NOT to use this skill

- ❌ You don't have usage telemetry yet — the skill consumes data, doesn't collect it. See [[ai-usage-telemetry-design]] for the collection side.
- ❌ You want to *judge* specific named people. The skill surfaces patterns; performance judgments based on AI usage are a different (and harder) decision.
- ❌ The input lacks every effectiveness field. You can still produce a volume report, but call out the limitation explicitly — don't ship a report that looks like effectiveness analysis when it isn't.
- ❌ Your team is < 5 people *and* the view is team-rollup. Aggregate views aren't anonymous at that size.

## Anti-patterns to avoid

- ❌ Inferring effectiveness from prompt length, prompt count, or session count alone. These measure *activity*, not *value*.
- ❌ Naming individuals in a team-rollup report — once a name appears in aggregate context, the report has crossed into per-user territory.
- ❌ Reporting on periods with too little data ("Mon–Tue only") and presenting it as a trend.
- ❌ Faking effectiveness columns when the input lacks them. Omit, don't estimate.
- ❌ Generating an "AI theater leaderboard" of named users. That's a workplace incident, not a report.
- ❌ Embedding the input prompts verbatim in the report. Prompts often contain sensitive content (code, customer data); the report works from metadata only.
- ❌ Comparing two periods that aren't normalized (e.g. a 7-day week against a 10-business-day window). If the script can't normalize, say so.
