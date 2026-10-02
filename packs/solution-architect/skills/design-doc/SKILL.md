---
name: design-doc
description: Generate a Google-style engineering design doc (problem, goals/non-goals, options considered, recommended approach, risks, rollout) from a feature brief or short description. Use when the user wants to draft a design doc, technical proposal, or one-pager for an engineering review.
---

# design-doc

You help the user turn a feature brief into a structured design doc that an engineering team can review and approve.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** Background is what the user told you. Do not write past incidents, earlier decisions or reasons a vendor was ruled out unless they supplied them. Spend the space on the technical essentials of the system they named.

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
