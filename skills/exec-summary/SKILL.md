---
name: exec-summary
description: Compress a long technical document, design doc, or proposal into a one-page executive summary aimed at non-technical or time-poor stakeholders. Use when the user has a long doc and needs a 30-second readable version, or is writing a 1-pager for a steering committee, partner, or executive sponsor.
---

# exec-summary

You help the user turn dense technical material into a one-page brief that a VP can read between meetings and act on.

## How to respond

1. **Get the source.** Either the user pastes the full doc, gives you a file path, or describes the project verbally. If the source is more than ~3000 words, ask them to confirm scope: "Is this for [audience X] who already knows [Y]?"

2. **Identify the audience.** A one-pager for an exec sponsor is different from one for finance is different from one for a partner. Default audience is "senior leader who is not an engineer, has 60 seconds, and needs to approve or push back."

3. **Use [`templates/exec-summary.md`](templates/exec-summary.md)** — six fixed sections:
   1. **The Ask** (one line — what decision/approval are we requesting?)
   2. **TL;DR** (three bullets — what's the project, why now, what's the recommendation)
   3. **Business impact** (revenue / cost / risk / time — quantified where possible)
   4. **Cost & timeline** (rough numbers — say "rough" if they are)
   5. **Risks & how we're managing them** (max 3 — pick the ones the exec would ask about)
   6. **What we need from you** (concrete asks — money, headcount, an exec decision, a connection)

4. **Compress ruthlessly.** A one-pager is **one page** — about 300–400 words rendered, including the headers. Cut:
   - Adjectives ("robust", "scalable", "next-generation")
   - Hedging ("we believe", "in many cases")
   - Technical jargon (replace or define inline once)
   - History the audience already knows

5. **Lead with the conclusion.** Execs read top-to-bottom and stop when they have what they need. The Ask + TL;DR must be self-contained — if those are all the exec reads, they should be able to make a decision.

## Quality bar

- **Quantify or qualify.** Numbers are best ("\$2.4M ARR at risk"), but if you don't have numbers, say "directional" rather than inventing precision.
- **Plain language.** A non-engineer should not encounter a term they don't recognize in the first paragraph.
- **No internal-team-speak.** "OKRs", "swimlanes", "north-star metric" are okay; "sharding strategy", "eventually consistent", "blue-green" need translation or replacement.
- **Active voice, second person where natural.** "You'll need to approve the budget" beats "budget approval will be required".

## Anti-patterns to avoid

- ❌ Burying the recommendation on page 2 of a 1-pager.
- ❌ Listing technical wins ("reduced p99 by 40ms") with no business translation.
- ❌ Risk sections full of generic risks ("scope creep", "team turnover"). Pick the *project-specific* ones.
- ❌ "Next steps: align with stakeholders." Empty calorie. Replace with the actual action.
- ❌ Asking the exec to "review the full design doc for details" without saying which sections matter.
