# Audience archetype matrix

Eight archetypes covering the common stakeholder-communication situations an architect runs into. Each has rules dense enough to drive concrete structural choices in `deck-builder`, `slide-outliner`, or `exec-summary`.

---

## `exec`

A single senior decision-maker (VP, SVP, C-suite) or a small leadership team. They have 15–30 minutes max and want to leave with a decision.

| Dimension | Rule |
|---|---|
| Slide count | 6–10 (decision review) or 3–5 (quick update) |
| Bullets / slide | 3 max |
| Words / bullet | ≤ 8 |
| Tone | Direct, opinionated, outcomes-first |
| Title style | **Assertion** — "Postgres meets our latency target" |
| Must-have sections | The Ask • TL;DR • Business impact • Risks • What we need from you |
| Favour layouts | `big_number`, `content` (sparse), `closing` |
| Avoid layouts | `quote` (rarely lands), dense `two_column` |
| Never include | Technical jargon without translation, "team" slides, agenda slides |

**Opening rule:** First slide after the cover must state the Ask. If the exec stops listening after slide 2, they should still know what you wanted.

---

## `board`

Board of directors or steering committee. Quarterly cadence, mixed business/financial fluency, often skim before the meeting.

| Dimension | Rule |
|---|---|
| Slide count | 8–12 (quarterly) |
| Bullets / slide | 3 max |
| Words / bullet | ≤ 6 |
| Tone | Polished, business-led, transparent about risks |
| Title style | **Outcome** — "$24M ARR protected by Q3" |
| Must-have sections | Cover • TL;DR • Strategic context • Financials • Risks • Ask |
| Favour layouts | `big_number`, `two_column` (before/after), `quote` (testimonials), `closing` |
| Avoid layouts | Dense `content` slides |
| Never include | Hidden bad news, sandbagged numbers, unfounded optimism |

**Risk rule:** Always include a risks slide with mitigations. Boards trust presenters who name risks; they distrust presenters who pretend there are none.

---

## `technical`

Engineering peers, architecture review, design review, staff/principal-level audience. Wants depth, expects pushback.

| Dimension | Rule |
|---|---|
| Slide count | 12–20 (full design review) |
| Bullets / slide | 5–6 |
| Words / bullet | ≤ 14 |
| Tone | Precise, neutral, evidence-first |
| Title style | **Descriptive ok** — "Migration approach" — or assertion |
| Must-have sections | Context • Goals/non-goals • Proposal (3–5 slides) • Alternatives considered • Risks • Rollout • Open questions |
| Favour layouts | `content`, `two_column` (compare options), `section` (chapter breaks) |
| Avoid layouts | `big_number` (overkill), `quote` (out of place) |
| Never include | Hand-waving on hard problems, "trust me" assertions without evidence |

**Alternatives rule:** Always show at least 2 alternatives with why-not. Skipping this section is the single biggest credibility killer in a technical review.

---

## `sales`

Customer or prospect in a pre-sale or expansion conversation. Mixed business/technical, optimising for "what does this do for me".

| Dimension | Rule |
|---|---|
| Slide count | 8–12 |
| Bullets / slide | 3–4 |
| Words / bullet | ≤ 10 |
| Tone | Story-arc, benefits-led, social proof |
| Title style | **Benefit-led** — "Cut close time by 40%" |
| Must-have sections | Hook • Their pain (in their language) • Our solution • Proof (logos/quotes) • Pricing tease • Close |
| Favour layouts | `big_number` (proof points), `quote` (customer testimonials), `two_column` (before/after) |
| Avoid layouts | `section` (kills momentum), dense `content` |
| Never include | Feature lists without business translation, internal roadmap detail, competitor bashing |

**Hook rule:** Slide 2 must be about *their* problem, not about us. If we don't earn their attention here, the rest of the deck is wasted.

---

## `investor`

Fundraising audience — VCs, angels, strategic investors. Cynical, pattern-matching, looking for reasons to say no.

| Dimension | Rule |
|---|---|
| Slide count | 10–15 (full deck), 5–7 (teaser) |
| Bullets / slide | 3–4 |
| Words / bullet | ≤ 10 |
| Tone | Confident, evidence-heavy, narrative-driven |
| Title style | **Assertion + number** where possible |
| Must-have sections | Problem • Market • Product • Traction • Business model • Team • Ask |
| Favour layouts | `big_number` (traction, market size), `content`, `two_column` (us vs. status quo) |
| Avoid layouts | `section` (slows momentum), `closing` (use a definite Ask slide instead) |
| Never include | TAM math without bottom-up validation, vanity metrics, "no competition" claims |

**Team rule:** Team slide goes near the end (after traction) — investors evaluate the team *in the context of* what the team has built, not as an opening trust statement.

---

## `internal`

All-hands, team meetings, alignment sessions. The audience already trusts the presenter and shares context.

| Dimension | Rule |
|---|---|
| Slide count | 5–10 |
| Bullets / slide | 4–5 |
| Words / bullet | ≤ 12 |
| Tone | Collaborative, candid, action-oriented |
| Title style | **Topic ok** — "Q3 priorities" |
| Must-have sections | Context (often skip — they know it) • Proposal • Discussion topics • Action items |
| Favour layouts | `content`, `two_column`, brief `quote` (e.g. customer signal that motivated the change) |
| Avoid layouts | `closing` (instead end on "discussion") |
| Never include | Over-polished language that suggests the deck is also for an external audience |

**Discussion rule:** End on a slide that *invites* discussion — listed questions, decisions to make as a group, etc. — not a thank-you.

---

## `partner`

Joint meeting with a strategic partner, channel, integrator, or co-seller. Both sides have agendas.

| Dimension | Rule |
|---|---|
| Slide count | 8–12 |
| Bullets / slide | 3–4 |
| Words / bullet | ≤ 10 |
| Tone | Mutual benefit, joint outcomes |
| Title style | **Mutual benefit** — "Joint customers see X% faster onboarding" |
| Must-have sections | Mutual context • What we're each bringing • Joint outcomes • Concrete next steps |
| Favour layouts | `two_column` (us / them or before / after), `quote` (joint customer if you have one) |
| Avoid layouts | Roadmap detail beyond integration touchpoints |
| Never include | One-sided "what we offer" pages, internal strategy detail |

**Reciprocity rule:** Every slide should reference *both* sides' contribution, not just ours. If a slide is fully about your company's product, it doesn't belong here.

---

## `customer`

Existing customer in QBR, renewal conversation, or success check-in. Audience knows the product, wants to know "what's next for me".

| Dimension | Rule |
|---|---|
| Slide count | 6–10 (QBR), 3–5 (success check-in) |
| Bullets / slide | 3–4 |
| Words / bullet | ≤ 12 |
| Tone | Outcomes (theirs), partnership tone |
| Title style | **Outcome for them** — "You'll save 12 engineer-hours/week" |
| Must-have sections | Their results to date • What's new for them • What's next together • Asks (both sides) |
| Favour layouts | `big_number` (their numbers), `two_column` (last quarter / next quarter), `content` |
| Avoid layouts | `section`, dense roadmap pages |
| Never include | Generic product updates not relevant to this customer, churn-flavoured language |

**Specificity rule:** Every number on this deck should be *their* number, not industry averages or aggregated benchmarks.

---

## Picking when audiences mix

When you have a mixed room ("VP Eng + the partner CTO + their procurement lead"):

1. Identify the *decision-maker* — the person whose yes/no matters most. That's your archetype.
2. Add an **appendix** with the depth the technical attendees will want.
3. Don't try to serve every archetype in the main flow — you'll satisfy none of them.

Exception: for a `technical + exec` mix where both are key decision-makers, use `exec` for the main flow and put technical detail in slides labelled as appendix. Engineers tolerate light main decks more than execs tolerate heavy ones.
