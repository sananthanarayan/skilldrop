# Example: Weekly engineering-team rollup

A small synthetic event log demonstrating the three views — including graceful degradation when optional fields are missing and the privacy-floor refusal on `team-rollup` for small teams.

## Input — `events.csv`

```csv
timestamp,user,tool,session_id,output_consumed,consumed_at,outcome
2026-05-19T09:14:23Z,alice@acme.com,claude-code,sess-001,1,2026-05-19T11:02:00Z,success
2026-05-19T09:14:55Z,alice@acme.com,claude-code,sess-001,1,2026-05-19T11:02:00Z,success
2026-05-19T09:18:02Z,alice@acme.com,deck-builder,sess-001,1,2026-05-19T14:30:00Z,success
2026-05-19T10:01:11Z,bob@acme.com,cursor,sess-014,0,,success
2026-05-19T10:01:30Z,bob@acme.com,cursor,sess-015,0,,success
2026-05-19T10:02:11Z,bob@acme.com,cursor,sess-016,0,,success
2026-05-19T10:03:11Z,bob@acme.com,cursor,sess-017,0,,success
2026-05-19T10:04:11Z,bob@acme.com,cursor,sess-018,0,,success
2026-05-20T14:22:08Z,carol@acme.com,claude-code,sess-029,1,2026-05-22T08:11:00Z,success
2026-05-20T15:22:08Z,carol@acme.com,adr-generator,sess-029,1,2026-05-22T08:11:00Z,success
2026-05-20T16:22:08Z,carol@acme.com,design-doc,sess-030,1,2026-05-22T08:11:00Z,success
2026-05-19T11:14:23Z,dan@acme.com,claude-code,sess-101,1,2026-05-19T13:00:00Z,success
2026-05-19T11:15:23Z,dan@acme.com,claude-code,sess-101,0,,success
2026-05-20T08:14:23Z,eve@acme.com,claude-code,sess-201,1,2026-05-20T09:00:00Z,success
2026-05-20T08:15:23Z,eve@acme.com,claude-code,sess-201,1,2026-05-20T09:00:00Z,success
2026-05-20T08:16:23Z,eve@acme.com,cursor,sess-202,1,2026-05-20T10:00:00Z,success
```

16 events, 5 users, 5 tools, period 2026-05-19 → 2026-05-20.

## Generate the three views

```bash
# Per-user (manager view, names individuals)
python3 scripts/build_report.py events.csv \
  --view per-user --from 2026-05-18 --to 2026-05-21 \
  --team-name "Acme Eng" -o out/per-user.md

# Team-rollup (aggregate, no names, safe for skip-level/exec)
python3 scripts/build_report.py events.csv \
  --view team-rollup --from 2026-05-18 --to 2026-05-21 \
  --team-name "Acme Eng" -o out/team-rollup.md

# Effectiveness (per-user template, sorted by descending single-shot rate)
python3 scripts/build_report.py events.csv \
  --view effectiveness --from 2026-05-18 --to 2026-05-21 \
  --team-name "Acme Eng" -o out/effectiveness.md
```

## Output — per-user view (excerpt)

```markdown
# AI Usage Report — Acme Eng

**Period:** 2026-05-18 → 2026-05-21 (3 days)
**Users in scope:** 5
**Total invocations:** 16

| User | Invocations | Sessions | Avg / session | Distinct tools | Effectiveness rate | Single-shot rate |
|---|---:|---:|---:|---:|---:|---:|
| alice@acme.com | 3 | 1 | 3.0 | 2 | 100% | 0% |
| bob@acme.com | 5 | 5 | 1.0 | 1 | 0% | 100% |
| carol@acme.com | 3 | 2 | 1.5 | 3 | 100% | 50% |
| dan@acme.com | 2 | 1 | 2.0 | 1 | 50% | 0% |
| eve@acme.com | 3 | 2 | 1.5 | 2 | 100% | 50% |
```

**Reading the data:**
- **Alice** — 3 invocations in 1 session, all consumed, 2 tools. Deep, engaged use.
- **Bob** — 5 invocations across 5 different sessions, 0% consumed, 1 tool only. **This is the AI-theater pattern**: high single-shot rate + low effectiveness + low breadth. Worth a conversation — *but the conversation, not the verdict.*
- **Carol** — varied tools, mixed effectiveness. Healthy exploratory pattern.
- **Dan** — small sample. Don't over-read.
- **Eve** — engaged use, good breadth.

## Output — team-rollup (excerpt)

```markdown
# AI Usage Rollup — Acme Eng

| Metric | Value |
|---|---:|
| Invocations / user / day (median) | 1.0 |
| Distinct tools per user (median) | 2 |
| Effectiveness rate (team avg) | 62% |
| Single-shot session rate (team avg) | 64% |
| Active users (≥1 invocation in period) | 5 of 5 |

| Engagement tier | Users | What it means |
|---|---:|---|
| **Heavy** (>20 invocations/week) | 0 | … |
| **Moderate** (5–20 / week) | 4 | … |
| **Light** (1–4 / week) | 1 | … |
| **Inactive** (0 / week) | 0 | … |
```

No names appear. The "Bob is doing AI theater" insight is invisible from this view by design — if a manager needs that signal, they switch to `per-user` and take ownership of the privacy boundary.

## Demonstrating graceful degradation

If the input is missing optional fields, columns drop silently to `—`:

```csv
timestamp,user,tool
2026-05-19T09:14:23Z,alice@acme.com,claude-code
2026-05-19T09:14:55Z,alice@acme.com,claude-code
```

```markdown
| User | Invocations | Sessions | Avg / session | Distinct tools | Effectiveness rate | Single-shot rate |
| alice@acme.com | 2 | — | — | 1 | — | — |
```

The "Where signals are missing" section then explains *what* couldn't be computed and *why*.

## Demonstrating the privacy floor

With fewer than 5 users in scope, `team-rollup` refuses to generate:

```
$ python3 scripts/build_report.py small_team.csv --view team-rollup ...
error: team-rollup requires ≥5 users in scope; got 3. Aggregate views aren't
anonymous at that size. Use --view per-user and treat the output as identifying.
```

This is the contract — the tool won't be the one to anonymize-by-accident a team that's too small to be anonymous.

## Hand-off to the user (what the agent would say)

> Generated `out/per-user.md` — 5 users, 16 invocations, period 2026-05-19 to 2026-05-20.
>
> Two things to know before reading:
> 1. **All optional signals were present**, so the report includes effectiveness and single-shot columns. The numbers are real, not estimated.
> 2. **The most actionable pattern** is in the single-shot + effectiveness columns. One user shows 100% single-shot and 0% effectiveness — a starting place to ask about engagement, *not* a verdict on intent. The report flags the pattern; interpretation is yours.
>
> Want me to also produce the team-rollup view? It hides individual names and is safer for broader audiences.
