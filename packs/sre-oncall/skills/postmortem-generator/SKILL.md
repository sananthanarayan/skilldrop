---
name: postmortem-generator
description: Write a blameless incident postmortem from the raw material (chat scrollback, alert history, timeline, notes) for the audience and length the user names — the cause stated as the change and the gap that let it through, never a person even when the notes name one; who or what noticed first and how late; known kept apart from still-unknown; and follow-up actions that close the gap. Invents no times, figures, owners or severities. Use after an incident or outage when the user needs a postmortem, RCA, incident review, a plain explanation for a non-technical reader, or "lessons learned" doc.
---

# postmortem-generator

**The rule: name the change and the missing check, never the person.** Incident notes are
written in the heat of it: "Dana's deploy broke it", "Sam forgot the flag". The agent's habit
is to carry that framing straight into the document, and a postmortem that names someone as
the cause teaches everyone to hide the next mistake. The cause is always a condition: what
made the error easy to make, hard to catch and quick to spread. People appear only doing
response work, by role ("the on-call engineer rolled back at 14:32"), and that holds even when
the user's own message points at someone.

A second rule sits beside it: **say plainly who or what noticed first, and how late.** If a
customer, a support ticket or a member of staff found the problem before any alert did, that
is the most useful sentence in the document: ✅ *"Two teachers reported the gradebook down 40
minutes before any alert fired."* Don't write "alerting worked" when it didn't.

## How to respond

1. **Fit the audience and length they asked for.** "Half a page for the board", "a note for
   customers", "two pages max", "the full incident review": that is the format. A
   short version is what happened, why it was possible, how it was found, and what changes.
   The full form in [`templates/postmortem.md`](templates/postmortem.md) is for when they ask
   for a full review or an incident-review meeting doc.

2. **Build the timeline from the material.** Use the events that changed what users saw:
   impact starts, first noticed, mitigation, impact ends. Use the timezone the material uses
   unless asked otherwise, and state it. Compute the gaps that matter (start to noticed,
   noticed to fixed) only from times you have.

3. **Keep what is known apart from what is still being investigated.** Write the cause the
   evidence supports, and name anything not yet confirmed as open.

4. **Write the causes as conditions, more than one where the material shows more than one.**
   For each: the condition, and why it made the incident possible or worse. ✅ *"A config value
   passed review and deploy; nothing validates that field."* ❌ *"Human error"*, ❌ *"should
   have been more careful"*. Don't invent extra causes to make up a number.

5. **Follow-ups that close the gap.** Each action says what changes and how anyone could tell
   it's done: ✅ *"Config deploys reject values that fail the schema, checked by a test deploy
   of a bad value."* ❌ *"Improve config safety."* Give an owner or date only if the material
   gives one; otherwise write "no owner yet". A few strong actions beat a long list.

6. **Runbook changes, when the incident proved a procedure wrong or missing.** Phrase each as
   a concrete edit to the runbook section it affects, ready for someone to apply. Leave them
   out of a short version for a non-technical audience unless asked.

7. **Say only what the material supports.** No affected-customer count, revenue or SLA-credit
   figure, severity level, owner or time that isn't in it, even when a stakeholder asked for
   one. Where a number was asked for and the material can't give it, say what it does show
   ("12 customers have written in so far") and what would settle it. Never leave
   `[missing]` or blank fields in the document; list what is still unknown once, briefly,
   after it.

8. **Deliver from what you have.** With notes to work from, write it and state any assumption
   in one line. With nothing to work from, ask in two sentences for the timeline, how it was
   noticed, and what was done.

## Quality bar

- **No person is named as a cause.** Roles appear in response actions only, including when
  the user's notes name someone.
- **Who or what noticed first is stated,** with the gap to the first alert when the material
  gives both times.
- **Known and still-open are kept apart.**
- **Causes are conditions, not "human error",** and come only from the material.
- **Every action is checkable,** and has an owner only if the material named one.
- **Nothing is invented:** no figures, times, severities, owners or counts beyond the input.
- **The length and format are the ones asked for,** and the document has no placeholders.

## When to use this skill

- ✅ After an incident or outage, turning the response scrollback into the postmortem
- ✅ "Write the RCA for yesterday's outage"
- ✅ A short explanation of what went wrong for a non-technical reader
- ✅ Preparing the incident-review meeting doc

## When NOT to use this skill

- ❌ During the incident — mitigate first; live updates to stakeholders are `incident-comms`
- ❌ A performance-management record — the document is blameless by design; using it to blame kills honest reporting
- ❌ A project retrospective with no production incident
- ❌ Writing the runbook itself — hand the runbook changes to `runbook-generator`

## Anti-patterns to avoid

- ❌ **Copying the blame from the notes.** "The outage was caused by X's change" — rewrite as
  the change and the missing check.
- ❌ **"Alerting worked" when a customer found it first.** The detection gap is the finding.
- ❌ **Filling the template.** Severity rows, SLO burn, "where we got lucky" and owner columns
  on a half-page note for a head teacher.
- ❌ **Placeholders in a document meant to ship.** `Severity: [missing]` goes nowhere; list
  unknowns after the document.
- ❌ **Invented owners, dates and numbers** to make actions look tracked or impact look
  measured.
- ❌ **The 20-item action list.** Nobody finishes it and the important ones drown.
