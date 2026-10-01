---
name: requirements-interview
description: Generate per-stakeholder interview kits for feature discovery — ≤7 questions per stakeholder ranked by how much the answer changes the design, each naming the decision it informs, with at least one disconfirming question per script and an assumptions-to-validate ledger. Use when the user is gathering business requirements, preparing stakeholder or user interviews, or asks "what should I ask the sponsor/users/ops before we build this".
---

# requirements-interview

Builds the elicitation kit for the conversations *before* the PRD — so the answers come back in a shape `brief-intake` and `prd-draft` can consume, instead of as ten pages of agreement with the roadmap. The discipline: every question names the decision it informs, problems are asked about instead of solutions, and every script tries at least once to kill the feature.

## How to respond

1. **Pin the feature idea and identify the stakeholder cast.** From the idea, derive who holds which unknowns — typically: **sponsor** (success definition, constraints, appetite), **end users** (the actual workflow and workarounds — interview the people who do the work, not their manager), **ops/support** (failure modes, ticket reality, operational cost), **security/compliance/legal** (data constraints, regulatory floor), **finance/commercial** (pricing, cost ceiling) when money moves. Ask the user at most 2 questions — who's available, and what's already known — then build kits only for stakeholders who hold *open* unknowns. No interview exists to confirm what's already evidenced.

2. **Write ≤7 questions per stakeholder, ranked by design impact.** Rank 1 is the answer that most changes what gets built. Each question carries two annotations: **informs** (the decision) and **if-answer-is-X-then** (how the design moves). A question that wouldn't change anything regardless of answer doesn't make the seven. ✅ *"Walk me through the last time you handled a refund request — every tool you touched."* (informs: scope of integration; if 3+ tools → unified view is the core, not a nicety) — ❌ *"Would a refund dashboard be useful?"* (everyone says yes to free things).

3. **Ask about problems and the past, never solutions and the hypothetical.** People are reliable witnesses of what they *did* and unreliable predictors of what they'd *use*. ✅ *"What did you do the last time X failed?"* — ❌ *"Would you use a feature that prevents X?"*. Solutions offered by stakeholders get recorded as evidence of pain, then converted back into the underlying problem.

4. **Include at least one disconfirming question per script** — the question whose answer could kill or shrink the feature: ✅ *"If this never gets built, what would you do instead — and how bad is that, honestly?"* / *"Who would be annoyed if we built this?"*. A kit with no kill-question is a confirmation ritual with a calendar invite.

5. **Add the workflow-walkthrough opener for end users.** First substantive question is always a concrete recent episode ("the last time", "yesterday's"), not a generality ("typically", "usually") — generalities retrieve self-image; episodes retrieve facts. Instruct the interviewer to capture **verbatim quotes** — they become the evidence tags in `prd-draft`.

6. **Build the assumptions-to-validate ledger.** Every assumption the feature idea rests on, each mapped to: which stakeholder's which question validates it, and **what answer falsifies it**. An assumption no question can falsify gets flagged — it needs data or a prototype, not an interview.

7. **Emit with [`templates/interview-kit.md`](templates/interview-kit.md)**: one kit per stakeholder (30-minute shape: opener episode → ranked questions → kill-question → "who else should I talk to"), the assumptions ledger, and the synthesis instruction — notes go to `brief-intake` (one brief per interview, then merge) and decisions surface via `decision-log`.

## Useful references in this skill

- [`templates/interview-kit.md`](templates/interview-kit.md) — per-stakeholder kit skeleton + the assumptions ledger

## Quality bar

- **≤7 questions per stakeholder, ranked**, each annotated with the decision it informs and how the answer moves the design. Unannotated questions don't ship.
- **Zero leading questions in discovery position.** Anything shaped "wouldn't it be great if…" or answerable with a polite yes fails the kit.
- **Every script contains a kill-question** — and the kit says what a kill-answer looks like, so the interviewer recognizes it instead of softening it.
- **End-user scripts open with a concrete recent episode**, never "typically".
- **Every assumption in the ledger has a falsification condition.** "We'll validate adoption appetite" without what-would-disprove-it is theater.
- **The synthesis path is named.** Kits that don't say where the notes go produce interviews that end at the notes.

## When to use this skill

- ✅ Discovery phase before a PRD — deciding what to ask whom
- ✅ "What should I ask the sponsor / users / ops about this feature?"
- ✅ A feature idea built on untested assumptions that interviews could falsify
- ✅ Preparing a requirements workshop's pre-read questions

## When NOT to use this skill

- ❌ The answers already exist in tickets, analytics, or support logs — mine those first; interviews are for what data can't say
- ❌ Synthesizing notes after the interviews — that's `brief-intake` + `decision-log`
- ❌ Writing the requirements themselves — `prd-draft`, after the interviews
- ❌ Usability testing of an existing design — different method; this is problem discovery

## Anti-patterns to avoid

- ❌ **The 25-question interrogation.** Past seven, answers degrade into politeness; the ranking exists because time runs out before questions do.
- ❌ **Confirmation safari.** Every question shaped so yes means "build it" — discovery that can't disconfirm isn't discovery.
- ❌ **Asking for the solution.** "What should we build?" outsources design to whoever's loudest; ask what hurts, design later.
- ❌ **Interviewing the manager about the worker's workflow.** Managers describe the process diagram; workers describe the workarounds — the requirements live in the workarounds.
- ❌ **Skipping ops/support.** They hold the failure-mode requirements nobody else knows exist, and they're the cheapest interview on the list.
- ❌ **Hypothetical futures.** "Would you use…" — the answer is always yes and always worthless; ask about the last time, not the next time.
- ❌ **One loud stakeholder = the requirements.** The kit covers the cast precisely so one vivid interview doesn't become the spec.
