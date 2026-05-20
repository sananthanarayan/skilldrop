---
name: audience-profile
description: Translate an audience type (exec, board, technical, sales, investor, internal, partner, customer) into structural rules — slide count, density, tone, must-have sections, things to avoid. Reusable across deck-builder, slide-outliner, and exec-summary. Use whenever a stakeholder communication deliverable is being designed for a specific audience.
---

# audience-profile

You help the user (or another skill) pick the right *shape* for a communication deliverable based on who's receiving it. This skill is mostly a structured reference — it converts a free-form audience description into a concrete set of rules.

## How to respond

1. **Map the free-form audience to an archetype.** Common ones in [`reference.md`](reference.md):

   | Archetype | Typical signals |
   |---|---|
   | `exec` | "VP", "C-suite", "leadership team", a *single* senior decision-maker |
   | `board` | "Board of directors", "board update", "quarterly business review" |
   | `technical` | "Engineering team", "architecture review", "design review", "tech-lead", "staff engineers" |
   | `sales` | "Customer pitch", "prospect", "sales meeting", "pre-sales" |
   | `investor` | "Series A", "VCs", "fundraising", "investor update" |
   | `internal` | "All-hands", "team meeting", "alignment session", "stand-up" |
   | `partner` | "Partner meeting", "joint customer", "channel partner" |
   | `customer` | "Customer success", "QBR", "renewal conversation", "onboarding" |

   When the user describes a *mixed* audience ("VP Eng plus their staff plus the partner CTO"), pick the **least technical** archetype — you can always add detail in an appendix, but you can't un-confuse a non-technical attendee with mid-deck jargon.

2. **Emit a structured profile.** When invoked, return the archetype's full ruleset:

   ```
   Audience archetype: <name>
   Slide count target: <range>
   Bullet density: <max bullets per slide>, <max words per bullet>
   Tone: <descriptor>
   Title style: <assertion / descriptive / outcome / benefit>
   Must-have sections: <ordered list>
   Layouts to favour: <list>
   Layouts to avoid: <list>
   Things to never include: <list>
   ```

3. **Be opinionated.** This skill exists to *make decisions* for the user. If they push back, fine — but don't hedge in the initial response. "Use a `big_number` slide here" beats "you could consider a `big_number` slide if you wanted to".

4. **Hand off cleanly.** When called from `deck-builder` or `slide-outliner`, the profile is *input* to that skill — don't try to build the artifact yourself.

## When to use this skill

- ✅ Before drafting a deck, exec summary, or design review.
- ✅ When the user describes the audience vaguely ("a leadership meeting") and you need to make density/length decisions.
- ✅ When you need to challenge a prior draft ("this is too dense for an exec audience").

## When NOT to use this skill

- ❌ For peer engineering communication where the "audience" is just "another engineer reading the doc". The standard documentation style is fine.
- ❌ For purely internal artifacts (ADRs, runbooks) — those have their own conventions independent of audience.

## Useful references

- [`reference.md`](reference.md) — full archetype matrix with all eight profiles

## Quality bar

- **Profile output is concrete.** "Slide count: 8–12" beats "keep it short".
- **Mixed audiences resolve to the least-technical archetype**, with the more-technical detail moved to an appendix.
- **Don't invent new archetypes** for a single use case — pick the closest one and note the divergence ("`board`, but they've asked for technical depth on the proposal — add a 'how it works' section between Financials and Risks").
