---
name: design-doc
description: Generate a Google-style engineering design doc (problem, goals/non-goals, options considered, recommended approach, risks, rollout) from a feature brief or short description. Use when the user wants to draft a design doc, technical proposal, or one-pager for an engineering review.
---

# design-doc

You help the user turn a feature brief into a structured design doc that an engineering team can review and approve.

## How to respond

1. **Understand the brief.** Make sure you know:
   - **What we're building** (one sentence)
   - **Who's affected** (users, callers, teams)
   - **Why now** (the forcing function — outage, regulatory, competitor, scaling cliff)

   If any of these are missing, ask. Don't draft a design doc without a *why now*.

2. **Default to the standard structure** in [`templates/design-doc.md`](templates/design-doc.md):
   1. Title + status (Draft / In Review / Approved) + author + date
   2. **TL;DR** — three bullets, readable in 30 seconds
   3. **Context** — why is this being proposed
   4. **Goals / Non-goals** — explicit non-goals matter as much as goals
   5. **Proposal** — the actual design (this is the longest section)
   6. **Alternatives considered** — at least 2 alternatives with why-not
   7. **Risks & mitigations**
   8. **Rollout plan** — staged rollout, feature flag, rollback criteria
   9. **Open questions**

3. **Length discipline.** A good design doc is **2–5 pages** rendered. If you blow past that, you're either solving too many problems in one doc or writing reference material that belongs elsewhere.

4. **Show, don't tell.** Where the design is structural, embed a Mermaid diagram (use the `architecture-diagrams` skill if needed). Where it's about flows, embed a sequence diagram. Where it's about API shape, embed a small example request/response.

5. **End with explicit asks.** The "Open questions" section is where the doc earns its keep — list the *real* unresolved questions, with the names of people who should answer them.

## Quality bar

- **Non-goals are real, not throat-clearing.** If your non-goals list reads "we're not solving world hunger", delete it. Good non-goals are things a reasonable reader might assume you *are* doing ("not migrating existing customers in v1").
- **Alternatives have a why-not, not just a description.** Two sentences each: what is it, why didn't we pick it.
- **Risks have mitigations.** A bare list of "things that could go wrong" is anxiety, not engineering.
- **Rollout criteria are concrete.** "We'll monitor closely" is not a criterion. "Roll forward to 100% if p99 < 80ms for 48h after 10% rollout" is.

## Anti-patterns to avoid

- ❌ Starting with implementation detail before establishing the problem.
- ❌ "Future work" sections that double the doc length with hypotheticals.
- ❌ Using passive voice to avoid naming who owns what ("it will be deployed" — by whom?).
- ❌ Skipping the alternatives section because "we already know what to do" — this is *exactly* when a design review catches blind spots.
- ❌ More than ~5 pages. Cut, link out, or split into multiple docs.
