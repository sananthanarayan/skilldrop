# Brief: Decision Log

> Target downstream skill: `decision-log`

This brief is lightweight — most of `decision-log`'s work is *its own* extraction. `brief-intake` mostly normalizes the source before handing it over.

## Source
- **Type:** {Slack thread | meeting transcript | email chain | Notion page | mixed} [explicit|implied|inferred|missing]
- **Date of meeting / thread:** {YYYY-MM-DD} [explicit|implied|inferred|missing]
- **Attendees / participants:** {names if stated, "unknown" otherwise} [explicit|implied|inferred|missing]
- **Length:** {word count or minutes if known} [inferred]

## Scope the user wants extracted
- [ ] Decisions
- [ ] Action items
- [ ] Open questions
- [ ] Risks raised

(Default: all four if user didn't specify.)

## Today's date
{YYYY-MM-DD} — needed for converting relative dates ("next Friday", "EOQ") to absolute. [explicit]

## Sprint / fiscal context
- **Current sprint ends:** {YYYY-MM-DD} [explicit|implied|inferred|missing]
- **Quarter ends:** {YYYY-MM-DD} [explicit|implied|inferred|missing]

## Cleaned source
{Paste the source with the obvious noise stripped — greetings, off-topic banter, emoji-only messages. Keep ambiguous parts; decision-log decides what's load-bearing.}

---

## 🚩 Missing for downstream
- {e.g. "No date — decision-log can't convert 'Friday' to an absolute date"}
- {e.g. "Attendees unknown — owners can't be attributed to names"}
