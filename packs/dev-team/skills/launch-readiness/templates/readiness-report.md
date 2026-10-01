# Launch readiness — {change name}

**Change:** {PR / tag / feature} · **Reach:** {internal / N% / cohort / everyone} · **Release owner:** {role}
**Assessed:** {YYYY-MM-DD} · **Inputs:** {what was read — diff, design doc, migration plan, dashboards}

> **Assumptions to confirm first** (omit if none)
> - `[assumption]` {fact guessed rather than given}

## New failure modes

What this change, specifically, could do to users or data once live.

| # | Failure mode | Who is hurt | Reversible? |
|---|---|---|---|
| F1 | {e.g. backfill locks `orders` table under peak write load} | {checkout users} | {yes / no / partly} |
| F2 | | | |
| F3 | | | |

## Checks

Status is `met`, `not met`, or `n/a — <reason>`. No evidence means `not met`.

| # | Check | Covers | Status | Evidence | Owner |
|---|---|---|---|---|---|
| 1 | **Rollback** — tested path back, data story stated | all | | {link / command output} | {role} |
| 2 | **Detection** — an alert per failure mode, fires before users complain | F1–F3 | | | |
| 3 | **Response** — a runbook entry per alert in row 2 | F1–F3 | | | |
| 4 | **Quality targets** — each NFR target measured, not asserted | | | | |
| 5 | **Data & privacy** — sign-off for new personal data, retention, or processors | | | | |
| 6 | **Comms** — release notes drafted, support briefed, status-page owner known | | | | |
| 7 | **Exposure** — first exposure staged, or why all-at-once is safe | | | | |

## Open items

One line per `not met` row: what closes it, who, by when, and the hand-off if any.

- Row {n}: {what closes it} — {owner role}, {date} → {`migration-plan` / `observability-plan` / `runbook-generator` / none}

## Verdict

**{PROCEED | PROCEED WITH CONDITIONS | REVISE | BLOCKED}** — {the one reason, naming the row}.
