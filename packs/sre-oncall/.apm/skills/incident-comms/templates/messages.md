# incident-comms message templates

Paste-ready. Every message carries a next-update time — fill it or leave `[set HH:MM]`. Times in the customer's expected timezone (state it).

---

## ACKNOWLEDGE

### Customer (status page / in-app)
```
[Investigating] {Plain impact — what users can't do.} We're aware of the issue
and actively investigating. Next update by {HH:MM TZ}.
```
Example: *"[Investigating] Some users are unable to log in. We're aware and actively investigating. Next update by 14:15 ET."*

### Internal (support / sales / CS)
```
🔴 {SEV} — {one-line impact}. Status: investigating, cause not yet identified.
What to tell customers: {the approved customer line above — nothing beyond it}.
Workaround: {one if it exists, else "none yet"}.
Do NOT: speculate on cause or give a fix ETA.
Next update: {HH:MM}.
```

### Exec
```
{SEV} incident, started {HH:MM}. Impact: {who/how many/what business function}.
Exposure: {revenue / SLA / key accounts if known, else "assessing"}.
We need: {nothing right now / a decision on X / comms approval}. Next update {HH:MM}.
```

---

## UPDATE (send on cadence — even with no change)

### Customer
```
[{Investigating|Identified|Monitoring}] {What changed, or "We're continuing to
investigate."} {If identified: "We've identified the cause and are working on a fix."}
Next update by {HH:MM TZ}.
```
No-change variant: *"[Investigating] We're still working to identify the cause. No customer-facing change yet. Next update by {HH:MM}."*

### Internal
```
🟠 {SEV} update — {what changed since last}. Current status: {vocabulary word}.
What to tell customers now: {updated line}.
Workaround: {current}.
Next update: {HH:MM}.
```

### Exec
```
Update on {SEV}: {one sentence on progress}. Impact now {growing/stable/shrinking}.
{Decision needed / still no action required}. Next update {HH:MM}.
```

---

## RESOLVE (only after verification across all affected paths)

### Customer
```
[Resolved] {What's restored} has been restored as of {HH:MM TZ}. The issue affected
{who} between {start} and {end}. {If anyone might still be affected: "If you continue
to experience problems, {action}."} We apologize for the disruption.
{SEV1/2 only: "A full post-incident review will follow."}
```

### Internal
```
🟢 Resolved {HH:MM}. Root cause: {one line if confirmed, else "under review"}.
Customer-facing window: {start–end}. If a customer still reports issues: {action/route}.
Postmortem owner: {role}, due {date}.
```

### Exec
```
{SEV} resolved at {HH:MM}, total customer-facing window {duration}. Impact: {final
quantified impact}. {SLA/credit implications if any}. Postmortem to follow by {date}.
```
Handoff: feed the timeline and impact into `postmortem-generator`.
