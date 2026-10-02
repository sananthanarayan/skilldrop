# Postmortem template

Summary first — it's the only section most readers finish. All timestamps UTC. Unknowns get `[missing]`, never prose camouflage.

```markdown
# Postmortem: {one-line incident title, symptom-first — "Checkout 500s for EU users", not "Config issue"}

**Status:** draft | reviewed | actions-tracked
**Severity:** SEV{1–4} · **Date:** {YYYY-MM-DD} · **Author role:** {e.g. incident commander}

## Summary

{3–5 sentences a director can repeat: what broke for whom, for how long, why in one
clause, and the headline fix. No jargon that needs the timeline to decode.}

## Impact

| Measure | Value |
|---|---|
| Duration (impact start → end) | {Xh Ym} |
| Users / customers affected | {number or %, or [missing]} |
| Requests failed / degraded | {number, or [missing]} |
| SLO / error budget burn | {e.g. "34% of monthly budget", or [missing]} |
| Revenue / contractual | {value, "none known", or [missing]} |

## Timeline (UTC)

| Time | Event | Source |
|---|---|---|
| {hh:mm} | {impact begins — state change, not Slack chatter} | {alert/log/deploy} |
| {hh:mm} | {first human aware} | {page/user report} |
| {hh:mm} | {mitigation applied} | … |
| {hh:mm} | {impact ends} | … |

**Detection gap:** {impact start → first human aware} — {if users reported it before
monitoring fired, say exactly that}
**Mitigation gap:** {detection → impact end}

## Contributing factors (2+; "human error" is not one)

1. **{Condition, not act}** — {why this made the incident possible/worse; the guardrail
   that was absent or didn't fire}
2. **{…}** — {…}

## What went well / poorly / where we got lucky

**Well:** {response behaviors worth repeating}
**Poorly:** {response-side gaps — paging, comms, tooling — not the cause itself}
**Lucky:** {mandatory — the near-miss: "happened at 3am low traffic", "the one engineer
who knew X was awake", "rollback happened to be safe"}

## Action items (≤8)

| # | Action | Class | Owner (role) | Done when |
|---|---|---|---|---|
| 1 | {specific change} | prevent / detect / mitigate | {team or role} | {verifiable condition} |

**Considered, not taken:** {candidate} — {one line why not}

## Runbook deltas

- {Runbook section} → {the edit this incident proves necessary — paste-ready}

## Open questions

- {anything still [missing] that follow-up should resolve, with who can answer it}
```
