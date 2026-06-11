# incident-comms reference — audience altitude, status vocabulary, cadence

## The three audiences (same facts, three altitudes)

| | Customer (status page / in-app / email) | Internal stakeholder (support, sales, CS) | Exec |
|---|---|---|---|
| **Leads with** | what you can't do right now | what to tell your customers | business impact + the ask |
| **Cause** | none until confirmed, and only if it helps them | confirmed-vs-suspected, plainly | one clause, only if it changes a decision |
| **Length** | 2–4 sentences | short + a "what to say" block | 3 sentences, max |
| **Includes** | impact, status, workaround if any, next update | all that + comms guidance (pause? relay? hold?) | revenue/SLA/customer exposure, decision needed, what you need from them |
| **Excludes** | jargon, internal names, blame, speculative ETA | raw engineering detail they can't use | technical narrative, play-by-play |
| **Forward risk** | assume it's screenshotted to social media | assume it reaches a customer verbatim | assume it's quoted in a board update |

## Status vocabulary (use precisely — these words mean specific things)

- **Investigating** — aware of impact, cause not yet identified. Don't guess the cause to fill space.
- **Identified** — cause confirmed, fix not yet applied or not yet effective.
- **Monitoring** — fix applied, watching to confirm it holds. NOT resolved.
- **Resolved** — restored and verified across all affected paths. Only after verification.

Never skip "monitoring" straight to "resolved" on a SEV1/2 — the watch window is what catches the relapse.

## Cadence by severity (the promise you must keep)

| Severity | Customer-facing impact | Update cadence | First ack target |
|---|---|---|---|
| SEV1 | full outage / data risk / payments down | every 30 min, even with no change | ≤ 15 min |
| SEV2 | major feature down, no workaround | every 60 min | ≤ 30 min |
| SEV3 | degraded, workaround exists | at identified + at resolved | ≤ 2 h |
| SEV4 | minor / cosmetic | resolved note only, or none | n/a |

The cadence is set when you send the first ack ("next update at HH:MM") and is then a commitment. If the window arrives with nothing new, send the no-change update — silence is read as loss of control.

## What's in your control vs not

- **In your control — commit to these:** the next-update time, the fact that you're on it, the current confirmed impact.
- **Not in your control — never commit to these:** the fix ETA, the root cause before confirmation, the all-clear before verification.

When someone demands "when will it be fixed?", the honest, defensible answer is the next-update time: *"We don't have a confirmed restore time yet. Our next update will be at 14:30 with progress."*

## The forward test

Before sending any message, ask: if this were screenshotted and posted publicly with our logo on it, would we stand behind it? If no — remove the speculation, the blame, or the jargon until yes.
