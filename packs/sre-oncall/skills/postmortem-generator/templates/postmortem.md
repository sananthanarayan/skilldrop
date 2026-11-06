# Full incident review

For when the user asks for a full postmortem or an incident-review meeting doc. Leave out any
section the material has nothing for; never fill one with a placeholder. List what is still
unknown after the document, not inside it.

```markdown
# Incident review: {symptom-first title — "Checkout failures for EU customers", not "Config issue"}

{Date} · {who it is for, if the user said}

## Summary

{3–5 sentences someone can repeat: what broke for whom, for how long, why in one clause,
how it was found, and the main change being made.}

## Impact

{What users could not do, for how long, and any figures the material gives. If a figure was
asked for and the material can't give it, say what it does show and what would settle it.}

## Timeline ({timezone})

| Time | What happened | Source |
|---|---|---|
| {hh:mm} | {impact begins} | {alert / log / deploy / ticket} |
| {hh:mm} | {first noticed, and by whom or what} | … |
| {hh:mm} | {mitigation} | … |
| {hh:mm} | {impact ends} | … |

**Found by:** {who or what noticed first; the gap to the first alert}
**Time to fix:** {noticed → impact ended}

## Why it was possible

1. **{Condition, not act}** — {why it made the incident possible or worse}
2. {…only as many as the material shows}

**Still open:** {causes not yet confirmed}

## What went well and what didn't

{Response-side only: paging, comms, tooling. Add "where we got lucky" if the material shows
a near-miss.}

## Follow-ups

- {What changes} — done when {how anyone could check}. Owner: {as given, or "no owner yet"}

## Runbook changes

- {Runbook section} → {the edit this incident shows is needed}
```
