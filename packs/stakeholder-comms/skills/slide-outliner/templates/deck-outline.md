# Deck outline — {Topic}

**Audience:** {who's in the room}
**Format:** {live presentation 30 min + Q&A / read-ahead doc / async share}
**Slot:** {meeting / forum + date}
**Target slide count:** {N main + ~5 appendix}

---

## Slide 1 — Cover

**Title:** {Topic — usually mirrors the project name, as a phrase not a question}
**Key points:**
- Presenter(s) + role
- Audience the deck is for
- Date

**Speaker notes:** *{Set the scene in one sentence: "We're here to get your decision on X."}*

---

## Slide 2 — Why we're here

**Title:** {The decision / approval / input being sought, as an assertion}
**Key points:**
- The Ask (one line)
- What's on the table today vs. out of scope
- How this fits with prior decisions (link to ADR / prior review)

**Speaker notes:** *{Anchor on the Ask. If you don't get past this slide, the audience still knows what you needed.}*

---

## Slide 3 — Current state

**Title:** {Assertion about the current state — "Our checkout pipeline tops out at 50 RPS"}
**Key points:**
- 2–3 facts about the current system
- The constraint or pain that's forcing the change

**Speaker notes:** *{Establish the *why now*. Not "this could be better" — what's actually broken or about to be.}*

---

## Slide 4 — Proposed approach (overview)

**Title:** {What we're proposing, as an assertion}
**Key points:**
- The one-sentence change
- Architecture diagram (use `architecture-diagrams` skill if needed)
- The 2–3 key design decisions

**Speaker notes:** *{Stay shallow here — depth is in the next slides. If the diagram is unfamiliar, walk through it.}*

---

## Slides 5–7 — Proposed approach (detail)

**Use one slide per major component or major decision.** Examples:
- Slide 5: Data model change
- Slide 6: Migration path from current state
- Slide 7: Observability / how we'll know it's working

*(Plan these from the actual proposal, not in advance.)*

---

## Slide 8 — Alternatives considered

**Title:** {Why our pick beat the strongest alternative}
**Key points:**
- Alternative #1: what it was, one-line why not
- Alternative #2: what it was, one-line why not
- (Skip weaker alternatives — they belong in the appendix)

**Speaker notes:** *{Show your work. An exec who's been pitched before will trust you more if you killed at least one obvious option for a non-obvious reason.}*

---

## Slide 9 — Risks & mitigations

**Title:** {Top risk, framed as something we have a plan for}
**Key points:**
- Risk → mitigation (×3)
- Honest "we don't know yet" callouts go here, not hidden

**Speaker notes:** *{Don't pretend there are no risks. Audiences trust presenters who say "here's what could go wrong and here's how we'd respond."}*

---

## Slide 10 — Cost, timeline, rollout

**Title:** {Headline number — "Q3 ship for $480k" or "12 weeks, 4 engineers"}
**Key points:**
- Effort estimate + confidence
- Calendar timeline (gantt / phase strip)
- Rollout phases with go/no-go criteria

**Speaker notes:** *{Be honest about confidence. "Rough" + a transparent number is more credible than precise-looking fake numbers.}*

---

## Slide 11 — What we need from you

**Title:** {The Ask, restated as an action}
**Key points:**
- Decision needed: {…}
- Budget needed: {…}
- People needed: {…}
- By when

**Speaker notes:** *{Close on this slide. Take questions here, not after a thank-you slide.}*

---

# Appendix (backup slides — only shown if asked)

## A1 — Cost detail
{TCO breakdown, vendor pricing, sensitivity}

## A2 — Security & compliance
{Threat model summary, data classification, regulatory implications}

## A3 — Migration plan detail
{Phased plan, rollback, customer-impact analysis}

## A4 — Why not {the obvious alternative}
{The deeper kill reason for the option people will ask about}

## A5 — Open questions
{What we're still working out — be explicit}
