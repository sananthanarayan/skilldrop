---
name: user-journey-map
description: Map a customer's end-to-end journey toward an outcome — 3–6 stages, each with actions, emotions, pains, and opportunities, plus a rendered Mermaid emotion arc and the ranked pain points design should attack first. Use when the user wants a journey map, customer experience map, "map the user's path through onboarding", touchpoint analysis, or "where do users feel friction".
---

# user-journey-map

Maps what one customer experiences on the way to one outcome — outside-in, frontstage only — and converts the map's pains into a **ranked improvement target**, because a journey map that ends as wall art has failed. The emotional low points get found and named (peak-end rule: users judge an experience by its worst moment and its ending, not its average), so downstream design knows exactly which two stages to fix first. Sibling of `architecture-diagrams` (systems, not people) and upstream of `prd-draft` / `user-story-splitter` when an opportunity becomes committed work.

## How to respond

1. **Anchor persona, outcome, and evidence level.** Ask at most 2 questions, spent on the weakest anchors: *"whose journey — one specific persona?"* and *"what outcome are they trying to reach?"* No persona or outcome → don't draft; a journey for "users" toward "using the product" has no stage boundaries. Non-interactive run (no user to ask): derive a specific persona and outcome from the input if defensible and tag them `[assumption]`; underivable → emit `BLOCKED: need persona + outcome` naming both. Tag the whole map's **evidence level**: `[observational]` (interviews, session recordings), `[survey/analytics]`, or `[assumption-based]` (team hypothesis). Assumption-based is legitimate — it's a hypothesis that directs research — but it must say so at the top, not masquerade as findings.

2. **Fix the journey's edges.** Start trigger (the event that puts the persona on this path — in their life, not on your site: ✅ *"payroll fails on the last Friday of the month"*) and end state (what "done" means *to the persona* — ❌ "completes checkout" if their outcome is "salary problem solved"). Wrong edges are the most common defect: starting at the landing page amputates the discovery pain, ending at purchase hides the abandonment cliff in activation.

3. **Divide into 3–6 named stages.** Stages are coarse phases of the persona's goal — *discover, evaluate, start, get value, return* — never screens or clicks. More than 6 stages means the altitude has dropped to flow level; that's `user-story-splitter` / flow-design territory, say so and re-chunk.

4. **Fill the four rows per stage** — this table is the artifact's core:
   - **Actions**: what the persona does, in their words, frontstage only. What the org does backstage ("support reviews the request") is out of scope — note it in the hand-off, don't map it.
   - **Emotion**: score 1–5 with the *reason*: ✅ *"2 — asked for the same information a third time"* — ❌ *"2 — frustrated"*.
   - **Pains**: friction, confusion, dead ends — each tagged with the step-1 evidence level if it differs from the map's default.
   - **Opportunities**: what would change the experience if the pain were removed — stated as an outcome, not a solution: ✅ *"never re-enter data the system already has"* — ❌ *"add autofill"* (that's a design decision that belongs downstream).

5. **Mark the peaks, then rank.** From the emotion row: the **1–2 steepest dips** and the **single highest peak**, plus the *ending* emotion (peak-end rule counts it double). Rank the opportunities: severity of the dip × how many personas/journeys hit it × evidence strength. Top 2 opportunities become the named improvement targets; the rest are listed but explicitly deprioritized — an unranked list re-delegates the judgment to the reader.

6. **Render and emit** with [`templates/journey-map.md`](templates/journey-map.md), in one message: the stage table, a Mermaid `journey` diagram (one `section` per stage, scored actions drawing the emotion arc), ranked opportunities with the two named targets, and hand-offs — target becomes committed work → `prd-draft` or `user-story-splitter`; measurement for a fix → `success-metrics`; backstage causes implicated → name them for the service owner. See [`examples/b2b-saas-onboarding.md`](examples/b2b-saas-onboarding.md) for the full pattern.

## Useful references in this skill

- [`templates/journey-map.md`](templates/journey-map.md) — stage table, Mermaid journey skeleton, ranked-opportunities block
- [`examples/b2b-saas-onboarding.md`](examples/b2b-saas-onboarding.md) — worked example: trial-to-activation journey, assumption-based, with ranked targets

## Quality bar

- **One persona, one outcome**, both named in the title. A map for "users" is a map of nothing.
- **The evidence level is declared at the top** and every pain that deviates from it is tagged individually.
- **Stage edges live in the persona's life**, not on the product's surface — the trigger precedes the product; the end state is the persona's outcome.
- **Every emotion score carries its reason.** A bare number row is decoration.
- **Opportunities are outcomes, not features.** The moment "add a button" appears, the map has started doing design's job without design's process.
- **The dips, the peak, and the ending are explicitly marked**, and exactly 1–2 opportunities are named as the targets. Ranking is the deliverable.
- **The Mermaid renders.** Scores 1–5, one section per stage — check syntax before emitting.

## When to use this skill

- ✅ "Map the customer journey through onboarding/purchase/support"
- ✅ "Where do users feel the most friction?" — with or without research data
- ✅ Before a redesign: agree on the as-is experience and where it hurts most
- ✅ Turning scattered user feedback into one shared picture of the path

## When NOT to use this skill

- ❌ Screen-by-screen interaction or flow design — that's below this altitude; the map hands off to it
- ❌ Internal/employee process mapping — this skill is outside-in; org-internal flows are a process diagram (`architecture-diagrams` sequence flows)
- ❌ Backstage service wiring behind the touchpoints — `reverse-architecture` / `architecture-diagrams`
- ❌ A committed feature needing requirements — `prd-draft`

## Anti-patterns to avoid

- ❌ **One stage per screen.** "Landing → Signup form → Email verify → Dashboard" is a screen list, not a journey — stages are phases of the persona's goal.
- ❌ **Mapping the org, not the customer.** "Support triages the ticket" is backstage; the customer's row says *"waits two days, chases twice"*.
- ❌ **Hypothesis dressed as research.** An assumption-based map presented without its tag poisons every decision built on it. The tag is load-bearing.
- ❌ **Happy-path-only journeys.** A map with no dip below 3 didn't look — errors, waits, and re-entry live in every real journey.
- ❌ **Solutioning in the opportunities row.** "Add SSO" pre-empts design with a guess; "signing in stops being the reason trials stall" keeps the problem open and measurable.
- ❌ **The unranked pain inventory.** Fourteen equal pains means the reader does the prioritizing — the map's whole job was to do it for them.
