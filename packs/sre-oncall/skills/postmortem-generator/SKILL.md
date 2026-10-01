---
name: postmortem-generator
description: Generate a blameless incident postmortem from raw material (Slack thread, pager timeline, notes) — quantified impact, UTC timeline with detection/mitigation gaps, contributing factors instead of a single root cause, and ≤8 verifiable action items. Use after an incident or outage when the user needs a postmortem, RCA, incident review, or "lessons learned" doc.
---

# postmortem-generator

Turns the debris of an incident — Slack scrollback, pager entries, half-remembered timestamps — into a postmortem the next on-caller learns from. Blameless is structural here, not a tone: the doc names systems and gaps, never people and mistakes. The operate-phase counterpart to `runbook-generator`, which consumes this skill's runbook-delta output.

## How to respond

1. **Ingest the raw material.** Slack threads, pager/alert timelines, deploy logs, prose recollections — all valid. Ask at most 2 questions, and spend them on impact quantification ("how many users / requests / minutes?") — it's the data people forget fastest and the section read first. Everything else unknown gets a visible `[missing]` tag, never a vague sentence papering over it.

2. **Strip blame structurally while drafting.** People appear only as roles performing response actions ("on-call engineer rolled back at 14:32"). Errors are attributed to the system that allowed them. ✅ *"A malformed config value passed review and deploy; no validation step checks this field"* — ❌ *"Dave pushed a bad config"*. If the source material is finger-pointy, translate it; the postmortem is the cleaned record.

3. **Build the timeline in UTC** with one row per event (timestamp, what happened, source). Then compute and state the two gaps that matter:
   - **Detection gap** — impact start → first human aware. If users noticed before monitoring did, say so in those words.
   - **Mitigation gap** — detection → impact ended.
   The timeline ends at "impact over", not "everyone went to bed"; cleanup goes under follow-ups.

4. **Write contributing factors, not a root cause.** Minimum 2, typically 3–5, using "why was that possible?" chains. **"Human error" is banned as a factor** — it is always the start of a question, never the answer: what made the error easy to make, hard to catch, and fast to propagate? Each factor states the condition, not the act.

5. **Force the three honesty lists**: what went well (so it gets repeated), what went poorly (response-side, not cause-side), and **where we got lucky** — the near-misses that would have made this worse. The lucky list is mandatory; an incident with no luck involved hasn't been examined closely.

6. **Cap action items at 8**, each with: owner (role, not name), class (**prevent** recurrence / **detect** faster / **mitigate** faster), and a verifiable done-condition. ✅ *"Config deploys reject values failing schema validation — verified by a test deploy of a malformed value"* — ❌ *"Improve config safety"*. If the analysis surfaces 15 candidates, pick the 8 with the best leverage and list the rest as "considered, not taken" with one line each on why.

7. **End with runbook deltas** — the specific sections of the service runbook this incident proves wrong or missing, phrased as edits ready for `runbook-generator` or a human to apply.

8. **Emit with [`templates/postmortem.md`](templates/postmortem.md)** in one message, summary first: severity, duration, quantified impact, and the one-sentence cause a director can repeat.

## Useful references in this skill

- [`templates/postmortem.md`](templates/postmortem.md) — the full doc skeleton with the gap calculations and action-item table

## Quality bar

- **Impact is numbers or `[missing]`.** Duration, users/requests affected, SLO burn, revenue if known. "Significant impact" is not a measurement.
- **No person is named in a causal sentence.** Roles appear in response actions only. One named-blame sentence fails the doc.
- **Detection and mitigation gaps are computed and stated.** They are the two numbers the next incident will be judged against.
- **At least 2 contributing factors, zero of them "human error".** A single root cause means the chain of "why was that possible?" stopped one question early.
- **Every action item is verifiable and owned.** A reader can check it's done without asking anyone's opinion; an item without a done-condition is a wish.
- **"Where we got lucky" is non-empty.** Naming the near-miss is how it gets fixed before it's the next incident's headline.

## When to use this skill

- ✅ After an incident/outage, turning the response scrollback into the postmortem doc
- ✅ "Write the RCA for yesterday's outage"
- ✅ Preparing the incident-review meeting doc
- ✅ Retroactively documenting an old incident before the details evaporate

## When NOT to use this skill

- ❌ During the incident — mitigate first; the postmortem starts when impact ends
- ❌ A performance-management record — the doc is structurally blameless; misusing it kills honest reporting
- ❌ Project retrospectives with no production incident — different ritual, different doc
- ❌ Writing the runbook itself — emit the deltas and hand to `runbook-generator`

## Anti-patterns to avoid

- ❌ **Single root cause.** "The config was wrong" explains nothing about review, validation, deploy gates, or blast radius — the four places to actually fix.
- ❌ **"Human error" / "should have been more careful".** Careful is not a control. Name the missing guardrail instead.
- ❌ **The 20-item action list.** It signals diligence and delivers nothing; nobody finishes it and the P1s drown.
- ❌ **Timeline theater.** Forty rows of who-said-what-in-Slack instead of the ten events that changed system state.
- ❌ **Quiet heroics as a fix.** "An engineer noticed by luck at 2am" is a detection gap wearing a cape — the action item is monitoring, not gratitude.
- ❌ **Skipping the postmortem because impact was "minor".** Near-misses are the cheapest lessons; severity gates the meeting, not the doc.
