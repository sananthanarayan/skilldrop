---
title: Measure your loops
summary: Turn on the opt-in, local-only run log, then see which gates pass first time, which keep looping back, and which end in BLOCKED.
kind: how-to
---

# Measure your loops

Every loop's gate gives a verdict: READY or NOT READY, SHIP IT or MAJOR REWRITE. Over a few
weeks those verdicts show where work really gets stuck. Maybe G2 fails first time on most
changes, or `discover` keeps sending PRDs back. The run log records them, on your machine only.

## Turn it on

Set one environment variable to a file path, in your shell profile or the project's `.envrc`:

```bash
export SKILLDROP_LOOP_LOG="$PWD/.skilldrop/loop-log.jsonl"
mkdir -p .skilldrop && echo ".skilldrop/" >> .git/info/exclude   # keep it out of git
```

Every loop's `LOOP.md` has a *Run log (opt-in)* section. When the variable is set, the agent
running the loop appends one JSON line after each gate:

```json
{"ts":"2026-10-01T14:03:00Z","loop":"build","stage":"verify","gate":"G2","verdict":"NOT READY","round":1}
```

That's all it records: no prompts, no code, no names. Nothing is sent anywhere. Unset the
variable and logging stops. Delete the file and the history is gone.

## Read it

```bash
npx skilldrop-cli loop-stats              # reads $SKILLDROP_LOOP_LOG
npx skilldrop-cli loop-stats --days 30    # the last 30 days only
npx skilldrop-cli loop-stats --json       # for a dashboard or a spreadsheet
```

```text
build  G2 (verify)
  6 verdict(s): NOT READY 3, READY 2, BLOCKED 1
  33% pass first time · 1 blocked · longest run 3 round(s)
```

Verdicts are classified with the shared vocabulary in `contracts/terminals.json`. A
conditional pass (SHIP WITH CHANGES, PROCEED WITH CONDITIONS) counts as passing first time.

## What to do with it

- **A gate that rarely passes first time** usually points upstream. If G2 keeps failing,
  look at the acceptance criteria coming out of `shape` before blaming the implementation.
- **Frequent BLOCKED** means a missing input. The verdict line says which stage; the loop's
  output names what was missing.
- **A gate that always passes** may not be checking anything. Read a few of its reviews.

The log is per machine. To compare across a team, have each person run
`loop-stats --json` and combine the results. Don't rank people by them: a hard change loops
more than an easy one.
