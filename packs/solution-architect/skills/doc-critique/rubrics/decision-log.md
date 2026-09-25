# Rubric: Decision Log

Mirrors `decision-log`'s quality bar. The test: can a reader who *didn't attend* act on this log without going back to the source?

## Blockers
- **Decisions and action items are in separate tables.** Mixing them defeats the audit trail.
- **Every action item has an owner (named person).** Unowned actions don't get done — they must at minimum be flagged as `unowned`, not pretended-owned.
- **Dates are absolute.** "Friday" / "next week" / "EOQ" without a `YYYY-MM-DD` conversion blocks tracking.
- **Source column present** with a verbatim 5–10 word snippet for every row. Without it, hallucination is undetectable.

## Major
- **Decisions are decisions, not opinions.** "I think we should X" is not a decision — only group-acknowledged conclusions count.
- **Active voice in actions.** ❌ *"ADR-0007 to be sent to legal"* ✅ *"Send ADR-0007 to legal"*
- **Risks-raised section present** when the source has any. Risks are the most likely follow-up agenda item.
- **Open questions have a candidate owner** to answer (even if "needs assignment").
- **Gaps section present.** Action items without owners or dates, decisions without rationale — all surfaced explicitly.

## Minor
- **Attendees listed.** Useful for "who else needs to be looped in on this follow-up?"
- **Meeting / thread date present** at the top.
- **Today's date used for relative conversions** — and noted in the doc.
- **Tables consistent** — same columns across all four sections.

## Nits
- Numbering across tables (`#` column).
- Table alignment / formatting.
- Name disambiguation when two people share a first name.

## Anti-patterns to flag (always major)
- "AOB" or generic catch-all entries with no specifics.
- Capturing every utterance — log is bloated and load-bearing items get lost.
- Hallucinated attendees, dates, or rationale not present in the source.
- Mixing the meeting's *discussion* (verbatim points) with its *outputs* (decisions/actions).

## What's working — look for
- Verbatim source quotes that prove the extraction is faithful.
- Unowned items flagged rather than silently assigned.
- Relative dates converted with `(implied)` markers.
- Risks raised in the meeting that aren't in any decision — saved for follow-up.
