---
name: prfaq
description: Write an Amazon-style PR/FAQ — the launch press release for a product that doesn't exist yet, plus the customer FAQ and internal FAQ that force the hard questions before engineering starts. Use when the user wants a PRFAQ, a working-backwards document, a "write the press release first" exercise, or needs to align stakeholders on what a product must be before committing a team to build it.
---

# prfaq

The working-backwards forcing function: write the launch press release *before* the product exists, then answer the questions a real customer and a skeptical insider would ask. If the press release can't be written specifically — a nameable customer, a problem in their words, a benefit you could measure — the product isn't ready to spec, and surfacing that is the deliverable. Sits upstream of `prd-draft` (requirements for a committed product) and `business-case` (invest/defer decision): the PRFAQ decides whether the idea deserves either.

## How to respond

1. **Pin the three anchors** — customer, problem, differentiator. Ask at most 2 questions, spent on the weakest anchors: *"Who exactly is the customer, and what do they do today instead?"* and *"What does this do that the thing they use today doesn't?"* A PRFAQ for "everyone" with a problem stated in industry jargon produces a marketing document, not a forcing function — don't start drafting until all three anchors are concrete. Non-interactive run (no user to ask): derive missing anchors from the input where defensible and tag them `[assumption]` at the top; an anchor with no defensible derivation → emit `BLOCKED: need <anchor>` naming what to rerun with, instead of fabricating a customer.

2. **Write the press release** — one page, datelined with a city and a realistic launch date; no product name exists yet → invent a plausible working name and mark it as a placeholder. The blocks:
   - **Headline**: product name + the customer benefit in one sentence. ✅ *"Acme Contracts cuts routine contract review from three days to twenty minutes for in-house legal teams"* — ❌ *"Acme launches AI-powered legal platform"*.
   - **Sub-headline**: the one key detail the headline compressed (who it's for, what it replaces, or the mechanism).
   - **Problem paragraph**: the customer's current pain *in their words*. ✅ *"I can't close a deal until legal clears the paperwork, and legal is three days behind"* — ❌ *"lack of operational visibility into contract workflows"*.
   - **Solution paragraph**: what the product does and what it does *differently* from the alternative the customer already uses. "AI-powered" is not a differentiator; the mechanism is.
   - **Leadership quote**: one sentence naming the strategic rationale, attributed to a role (*"our VP of Product"*), never a placeholder name. If the rationale can't be articulated, that's a finding — report it.
   - **Customer quote**: a named-persona customer describing the before/after in concrete terms — a specific moment, not adjectives.
   - **Call to action**: what the customer does next to get started.

3. **Derive the adoption hypothesis** — two lines that make the press release falsifiable:
   - **First-success event**: the one *customer* action that proves first value landed, observable within a session. ✅ *"Legal counsel approves their first AI-reviewed contract without re-reading it line by line"* — ❌ *"user completes onboarding"* — ❌ *"we launch to beta"* (that's the team's action, not the customer's).
   - **Repeat-value behavior**: what brings the customer back after first success.

   Can't name a first-success event → the problem paragraph is too vague; go back to step 2 before continuing.

4. **Write the customer FAQ** — 3–5 questions a real buyer asks before switching: price, switching cost, reliability, "how is this different from `<what they use today>`", data/privacy. Answer honestly, and **at least one answer must concede a real trade-off**. A FAQ where every answer is good news is an ad.

5. **Write the internal FAQ** — the questions a skeptical insider asks, each with a committed answer:
   - The **riskiest assumption** — the belief that, if wrong, kills the product — and how it will be tested first.
   - The **hardest technical or operational problem** and why it's believed solvable.
   - The **acquisition path** — how the first 10 customers concretely arrive (not "marketing").
   - The **success metric** — traceable to the first-success event from step 3. "User count" when first success is an approval event is a vanity metric; the metric must count the event.
   - **What would make us kill this** — a named condition, not "if it doesn't work out".

6. **Run the read-aloud pass, then emit** with [`templates/prfaq.md`](templates/prfaq.md): could a non-technical reader retell the problem and solution after one read? Is every claim in the press release either measurable or attributed? Anything failing gets rewritten before the artifact ships. Close with the hand-off line: idea survives → `prd-draft` (requirements) or `business-case` (the investment ask); riskiest assumption unproven → the test for it comes first.

## Useful references in this skill

- [`templates/prfaq.md`](templates/prfaq.md) — press release blocks, adoption hypothesis, and both FAQ skeletons

## Quality bar

- **The problem paragraph is in the customer's words.** If it contains a term the customer wouldn't say out loud, it fails.
- **The first-success event is behavioral and observable** — you could watch a session recording and mark the moment it happened.
- **The solution names a mechanism**, not a category. "Uses AI" describes a decade of products; what does *this one* do differently?
- **At least one customer-FAQ answer concedes a trade-off.** Honesty in the FAQ is what separates a forcing function from a pitch.
- **The internal-FAQ success metric counts the first-success event** — not sign-ups, not launches, not page views.
- **The kill condition is named.** A PRFAQ that can't say what failure looks like hasn't confronted the riskiest assumption.
- **No spec content.** Zero API shapes, acceptance criteria, or backlog items — those belong downstream in `prd-draft`.

## When to use this skill

- ✅ A product or feature concept exists but no team is committed yet — test the direction before the spec
- ✅ "Write the press release first" / "do a working-backwards doc" / "Amazon-style PRFAQ"
- ✅ Stakeholders disagree about what a product *is* — the press release forces one answer
- ✅ A founder or PM needs to discover whether an idea survives its own hard questions

## When NOT to use this skill

- ❌ The product is committed and needs requirements — that's `prd-draft`
- ❌ The question is invest/defer with costed options — that's `business-case`
- ❌ Real launch marketing copy for a product that exists — this is a thinking tool, not copywriting
- ❌ Org-level strategy or portfolio questions — `strategy-analysis`

## Anti-patterns to avoid

- ❌ **PRFAQ as a spec.** The moment acceptance criteria or API shapes appear, it's stopped forcing direction and started doing `prd-draft`'s job badly.
- ❌ **Jargon-laundered problems.** "Lack of cross-functional visibility" is how a vendor talks. "I can't tell if my team is blocked" is how a customer talks. Only the second belongs in the press release.
- ❌ **Placeholder quotes.** "[CEO name]: 'We're excited…'" defeats the exercise — the quote exists to force the strategic rationale into one attributable sentence.
- ❌ **Launch-as-adoption.** "Ship to beta" as first success conflates the team's delivery with the customer's value. First success is something the *customer* does.
- ❌ **Moat without mechanism.** Claiming defensibility without naming what makes it hard to copy — data advantage, network effect, workflow lock-in — is a wish wearing a strategy's clothes.
- ❌ **All-good-news FAQs.** If the customer FAQ reads like the pricing page, the hard questions were dodged and the document proves nothing.
