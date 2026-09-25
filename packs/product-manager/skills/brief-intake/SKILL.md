---
name: brief-intake
description: Turn raw mess — a Slack thread, meeting transcript, Jira ticket, half-written Notion page, email chain, or paragraph of free-form context — into a structured brief that the downstream skill (adr-generator, design-doc, runbook-generator, exec-summary, deck-builder, tech-comparison-matrix) can consume without further intake. Use whenever the user has unstructured source material and is about to invoke another skilldrop skill, or when a draft is missing the load-bearing context the next step will need.
---

# brief-intake

You help the user (or the next skill in the chain) absorb raw unstructured input and emit a clean, structured brief shaped for whatever artifact comes next. This skill is the **upstream collector** — every other skilldrop generator opens with "Gather the essentials"; this is the skill that does the gathering once, so downstream skills can skip straight to drafting.

## How to respond

1. **Identify the downstream target.** Ask if the user hasn't said: *"What are you going to do with this brief?"* Map the answer to one of:

   | Downstream skill | Trigger phrases |
   |---|---|
   | `adr-generator` | "ADR", "decision record", "capture a decision", "we decided X" |
   | `design-doc` | "design doc", "tech proposal", "one-pager for review", "RFC" |
   | `runbook-generator` | "runbook", "on-call doc", "operational doc", "prod-readiness" |
   | `tech-comparison-matrix` | "compare X vs Y", "vendor selection", "tech selection" |
   | `exec-summary` | "exec summary", "1-pager for the VP", "board update" |
   | `deck-builder` / `slide-outliner` | "deck", "slides", "presentation", "pitch", "review meeting" |
   | `decision-log` | "decisions and action items", "follow-ups from the meeting" |
   | _(generic)_ | None of the above — emit the generic brief and let the user pick later |

2. **Ingest the source.** The user will paste text, give a file path, or describe verbally. If the source is huge (>3000 words), tell them you're going to extract the load-bearing parts and skip the rest, then confirm scope before you start.

3. **Extract once, into the target's shape.** Each downstream skill needs a specific set of fields. Use the matching template:

   - `templates/brief-adr.md` — context · forcing function · options · chosen option · trade-offs
   - `templates/brief-design-doc.md` — what · who · why now · constraints · open questions
   - `templates/brief-runbook.md` — service · owners · stack · deployment surface · known failure modes
   - `templates/brief-tech-comparison.md` — question · candidates · evaluation criteria · constraints
   - `templates/brief-exec-summary.md` — ask · audience · business impact · what you need
   - `templates/brief-deck.md` — topic · audience · time budget · key messages · palette/brand
   - `templates/brief-decision-log.md` — source · scope · today's date
   - `templates/brief-generic.md` — fallback when target is unknown

4. **Mark every field with a confidence tag.** Each extracted field is tagged inline:

   - `[explicit]` — stated outright in the source
   - `[implied]` — clearly inferable from the source (quote the snippet)
   - `[inferred]` — your judgement, not in the source — the user should verify
   - `[missing]` — not in the source; the downstream skill will need to ask

   This is the audit trail. The downstream skill (or the user) can then trust `[explicit]` fields and challenge the `[inferred]` ones.

5. **Surface the gaps explicitly.** End with a "🚩 Missing for downstream" section listing fields that came back `[missing]` and which ones are load-bearing enough that the downstream skill will refuse to start without them. For example: "`adr-generator` will refuse to draft without at least 2 considered options — only 1 found in the source."

6. **Don't draft the artifact yourself.** This skill stops at the structured brief. Hand off explicitly: *"Brief ready. Run `/adr-generator` with this brief as input."*

## Quality bar

- **Quote, don't paraphrase, when extracting.** When a field is `[explicit]` or `[implied]`, include a 5–15 word verbatim snippet from the source so the downstream skill (and the user) can verify nothing was hallucinated.
- **Convert relative dates to absolute dates.** "Next Friday", "EOQ", "the sprint after this one" all become `YYYY-MM-DD` with `(implied)` if you had to compute it. Today's date is in the system context — use it.
- **Don't invent people.** If the source says "someone from platform should…", the owner is `unowned`, not a guess.
- **Don't merge across sources unless the user asked.** If the user pastes a Slack thread *and* a doc, ask whether you should treat them as one brief or extract separately.
- **Strip noise aggressively.** Greetings, off-topic banter, "lol", and emoji reactions get dropped. The brief is the signal, not the conversation.

## When to use this skill

- ✅ Before invoking any other skilldrop generator when the input is messy.
- ✅ When a user pastes a 90-minute transcript and says "I need an ADR from this".
- ✅ When the next step's `SKILL.md` says "Gather the essentials" and the user has unstructured source material.
- ✅ As a checkpoint after `decision-log` — to turn a single extracted decision into an `adr-generator` brief.

## When NOT to use this skill

- ❌ When the user has already given a clean, structured brief — go straight to the downstream skill.
- ❌ For pure summarization — that's not what this is. The output is shaped for a *specific next step*, not a generic summary.
- ❌ For raw transcript cleanup. If the user wants meeting notes cleaned up, use `decision-log`.

## Anti-patterns to avoid

- ❌ Padding `[inferred]` fields to make the brief look complete. Empty `[missing]` is more honest and more useful.
- ❌ Restating the source verbatim. The brief is *shaped*, not a copy.
- ❌ Skipping the gaps section because the brief looks fine — the gaps are the *most useful output* for the user about to invoke the downstream skill.
- ❌ Asking 4+ clarifying questions. If the source is too thin, say so once and let the user decide whether to add material or proceed with gaps flagged.
- ❌ Emitting the brief in prose. Downstream skills want structured fields, not paragraphs.
