---
name: service-blueprint
description: Build a service blueprint — per step, the evidence the customer sees, the customer's actions, frontstage staff and system actions, backstage actions, and support processes, separated by the lines of interaction, visibility and internal interaction, with fail points, wait times and owners marked — as a table plus a Mermaid diagram and the ranked fixes. Use when the user wants a service blueprint, "what happens behind the scenes when a customer does X", to find where a service breaks or stalls, or to take a journey map down to the people, systems and handoffs that deliver it.
---

# service-blueprint

Shows how a service is delivered, not just how it feels. Each customer step is lined up against what staff and systems do in front of the customer, what they do out of sight, and the processes that support them. Fail points and waits are marked where they happen. Builds on `user-journey-map`, which covers one persona's frontstage experience and emotions. The hand-off is the journey map's backstage note: when a pain's cause sits behind the line of visibility, the blueprint is where it gets found. This skill maps people, roles, systems and handoffs; for the technical architecture of the systems themselves, use `architecture-diagrams`.

## How to respond

1. **Get the scope in one message.** Ask at most 2 questions, spent on the weakest of: *which service and which scenario* (one customer type, one path, a start and end), and *what's known about the backstage* (teams, systems, SLAs, tickets, process docs). If a `user-journey-map` exists, take its persona, stages and customer actions as the top rows instead of asking. Default to the as-is service, not the ideal one. Tag the blueprint's evidence level: `[observed]`, `[documented]`, or `[assumption-based]`.

2. **Fix one scenario with clear edges.** One customer type, one path, a trigger and an end state: ✅ *"A home-insurance customer reports a burst pipe and gets paid"* — ❌ *"Claims"*. Name the happy path, and list variants (rejected claim, second visit) as separate blueprints or a note. A blueprint that tries to show every branch becomes unreadable.

3. **Lay out the customer actions first**, left to right, as the columns: 6–12 steps, in the customer's words. Every other lane hangs off these steps. If a `user-journey-map` was supplied, the steps sit inside its stages; keep its stage names as column groups.

4. **Fill the lanes, top to bottom, for each step:**
   - **Evidence:** what the customer sees, holds or receives (email, web page, letter, van, invoice).
   - **Customer actions.**
   - — *line of interaction* —
   - **Frontstage:** what staff or self-service systems do that the customer sees or talks to (agent on the phone, the app, the technician on site).
   - — *line of visibility* —
   - **Backstage:** what staff and systems do out of sight to make the frontstage work (assessor reviews photos, case is routed).
   - — *line of internal interaction* —
   - **Support processes:** systems, third parties and internal teams that backstage depends on (policy system, payments provider, contractor network).
   Name the **owner** (role or team, not a person) for every frontstage and backstage cell. An action with no owner is a finding.

5. **Mark fail points and waits.** ⚠ **Fail point**: where the step can go wrong, with the failure, its effect on the customer, and how often if known. ⏱ **Wait**: where the customer waits, with the duration (measured, SLA, or `[estimate]`) and whether they're told how long. Handoffs between teams across a lane boundary are the usual sources of both; mark every handoff. Look especially for waits the customer can't see the reason for.

6. **Trace the journey map's pains to their causes.** For each customer pain (from `user-journey-map` or the input), point to the backstage or support cell that causes it: ✅ *"Customer re-sends photos (pain) ← assessor can't see the portal uploads; they arrive by email to a shared inbox (backstage)"*. This trace is what the blueprint adds over the journey map.

7. **Rank the fixes.** Score each fail point and wait by customer impact × frequency × how many steps it touches. Name the top 2–3 as fixes with an owner and the lane they change. The rest are listed, explicitly not prioritised now. Fixes are stated as outcomes: ✅ *"Assessor sees uploads within minutes"*, not *"Buy a new CRM"*.

8. **Emit with [`templates/blueprint.md`](templates/blueprint.md)** in one message: scenario and evidence level, the blueprint table (lanes as rows, steps as columns, with the three lines drawn as separator rows), a Mermaid flowchart with one subgraph per lane, fail points and waits, the pain-to-cause trace, ranked fixes, and open questions. Check the Mermaid syntax before emitting. Hand-offs: a fix becomes committed work → `prd-draft`; the systems in the support lane need their technical design → `architecture-diagrams`; no journey map yet and the frontstage emotions matter → `user-journey-map` first. See [`examples/insurance-claim-blueprint.md`](examples/insurance-claim-blueprint.md).

**Non-interactive runs** (subagent, CI, headless): a missing backstage becomes `[assumption]` cells with the whole blueprint tagged `[assumption-based]`, and missing wait times are `[estimate]`. If the service or scenario can't be identified from the input, emit `BLOCKED: need the service and one customer scenario`.

## Useful references in this skill

- [`templates/blueprint.md`](templates/blueprint.md) — the blueprint table with the three lines, Mermaid skeleton, fail-point and wait tables, pain-to-cause trace
- [`examples/insurance-claim-blueprint.md`](examples/insurance-claim-blueprint.md) — worked example: a home-insurance claim built on a journey map, with fail points, waits and ranked fixes

## Quality bar

- **One scenario, one customer type**, with a trigger and an end state, named in the title.
- **All five lanes and all three lines are present.** Evidence, customer, frontstage, backstage, support; interaction, visibility, internal interaction.
- **Every frontstage and backstage action has an owner** (role or team), or is flagged as unowned.
- **Every handoff across teams is marked**, and fail points ⚠ and waits ⏱ are marked where they occur, with durations or `[estimate]`.
- **Customer pains are traced to backstage or support causes.**
- **2–3 fixes are ranked and named**, stated as outcomes, each with an owner and the lane it changes.
- **The table and the Mermaid diagram match**, and the Mermaid renders.
- **Nothing is invented.** Teams, systems, SLAs and durations not in the input are tagged `[assumption]` or `[estimate]`, and the evidence level is declared at the top.

## When to use this skill

- ✅ "What actually happens behind the scenes when a customer does X?"
- ✅ Finding where a service stalls, breaks or bounces between teams
- ✅ Taking a journey map's pain points down to their operational causes
- ✅ Designing a new service and agreeing who does what before launch

## When NOT to use this skill

- ❌ One persona's stages, emotions and pains, frontstage only — that's `user-journey-map` (run it first if the customer side isn't known)
- ❌ The technical architecture of the systems in the support lane — that's `architecture-diagrams`
- ❌ Requirements for a fix the blueprint found — that's `prd-draft`

## Anti-patterns to avoid

- ❌ **The everything blueprint.** Every branch and exception on one page. One scenario per blueprint; variants get their own.
- ❌ **Departments instead of actions.** A backstage cell that says "Claims team" says who, not what. Write the action and the owner.
- ❌ **No line of visibility.** Without it, nobody can see which delays the customer feels but can't explain.
- ❌ **Waits without numbers.** "Customer waits for assessment" hides whether it's an hour or three weeks. Give a figure or an `[estimate]`.
- ❌ **The ideal process, drawn as the current one.** Copying the process doc instead of what happens. Tag the evidence level honestly.
- ❌ **A tool as the fix.** "Implement a new CRM" isn't an outcome. Say what must be true for the customer.
- ❌ **Redoing the journey map.** Emotion scores belong in `user-journey-map`; the blueprint takes its steps and goes down, not sideways.
