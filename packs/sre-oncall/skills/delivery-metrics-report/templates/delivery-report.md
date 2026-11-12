# Delivery metrics: <service>, <from> to <to>

**Scope:** <service>, production only, <n> weeks (ISO weeks, Monday start, UTC).
**Metrics:** DORA's current names (change lead time, deployment frequency, change fail rate, failed deployment recovery time, plus deployment rework rate if computed), as defined at dora.dev. Time to restore service across all incidents is shown as context, not as the DORA metric.
**Sources:** <deployments export, incidents export, PR export: tool and date pulled>
**Assumptions to confirm:** <[assumption] lines, or "none">

## Summary

<Three sentences: the trend that matters most, the week it moved, and the next thing to check.>

## Metrics

<Paste the script's DORA table, duration table, weekly series and flow table unchanged.>

## Findings

1. **<Finding as a sentence with the number and the week.>** <Evidence: which rows or weeks.> **Next check:** <the concrete thing to look at, and the skill or person who owns it.>
2. ...

## Data gaps

- <Each metric not computed and the column that would enable it>
- <Skipped rows by reason, from the data-quality section>
- <Low-n distributions>

## What to measure next

- <One or two changes to the exports that would make the next report better, for example "link incidents to deploy_id in the incident tool">

<Not for comparing teams: these numbers describe this service against its own history. See reference.md section 5.>
