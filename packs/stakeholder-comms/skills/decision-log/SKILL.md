---
name: decision-log
description: Extract decisions, action items, owners, and due dates from meeting notes, Slack threads, design-review transcripts, or any unstructured discussion. Produces a clean structured log the user can paste into a doc, tracker, or ADR queue. Use when the user has notes/threads/transcripts and asks for a "decision log", "action items", "what did we agree", or "follow-ups".
---

# decision-log

You help the user turn messy meeting notes or threads into a structured log of what was decided, who owns the follow-up, and what's still open.

## How to respond

1. **Ingest the source.** The user will paste notes, give a file path, or share a transcript. If the source is huge (e.g., a 90-minute transcript), confirm scope: "Are you only interested in decisions, or also action items and open questions?"

2. **Extract four categories:**

   - **Decisions made.** Things the group agreed on — even if informal. Look for phrases like "we'll go with…", "let's do…", "agreed", "fine by me", "ship it". Capture the decision in active voice, with a one-line *why* if it's in the source.
   - **Action items.** Things someone agreed to *do*. Need an owner (a name), an action (a verb phrase), and ideally a due date. If the date is fuzzy ("by next week"), convert to an absolute date and flag it.
   - **Open questions.** Things explicitly *not* resolved. Include who needs to answer if it's stated.
   - **Risks raised.** Concerns that were aired but not resolved — useful for the next meeting's agenda.

3. **Convert fuzzy dates to absolute dates.** "Friday" → `YYYY-MM-DD`. "End of week" → `YYYY-MM-DD (EOW)`. "Next sprint" → ask the user when the next sprint ends if it's not in the source. Mark dates as `(implied)` when you've inferred them so the user can verify.

4. **Attribute every action item to a named person.** "Someone should…" is not a tracked action — flag those as "unowned" so the user can assign in the meeting.

5. **Output as four tables**, in this order:

   ```markdown
   ## Decisions
   | # | Decision | Why | Source |
   |---|---|---|---|

   ## Action items
   | # | Owner | Action | Due | Source |
   |---|---|---|---|---|

   ## Open questions
   | # | Question | Owner (to answer) | Source |
   |---|---|---|---|

   ## Risks raised (not yet acted on)
   | # | Risk | Raised by | Source |
   |---|---|---|---|
   ```

   The `Source` column quotes ~5–10 words from the original notes so the user can verify nothing was hallucinated.

6. **Surface gaps.** End with a "🚩 Gaps" callout listing:
   - Action items without an owner
   - Action items without a date
   - Decisions whose rationale isn't captured in the source
   - Anything where you weren't sure whether it was a decision or a discussion

## Quality bar

- **Don't invent ownership.** If the source says "we should email the legal team", don't pick a name. Flag as unowned.
- **Don't promote opinions to decisions.** "I think we should use Postgres" is not a decision unless the group acknowledged it.
- **Quote, don't paraphrase, the source column.** A 5–10 word verbatim snippet is the audit trail.
- **Active voice in the action column.** ✅ "Send PR for ADR-0007 to legal" — ❌ "ADR-0007 to be sent to legal".
- **Convert relative dates.** Today's date is needed — ask if unclear.

## Anti-patterns to avoid

- ❌ Mixing decisions and action items in one table. They're different.
- ❌ Capturing every utterance — pick the load-bearing ones.
- ❌ "AOB" or generic catch-all entries — be specific or drop.
- ❌ Hallucinating attendees, dates, or rationale that isn't in the source.
- ❌ Skipping the Gaps section because it looks like negative feedback — gaps are the most useful part for the meeting's follow-up email.
