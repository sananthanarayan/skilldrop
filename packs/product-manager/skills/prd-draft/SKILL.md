---
name: prd-draft
description: Draft a Product Requirements Document from a feature idea or brief — evidence-backed problem statement with zero solution language, testable MoSCoW-prioritized requirements, mandatory non-goals, and a success line per goal. Use when the user needs a PRD, wants to capture business requirements for a feature, or asks to turn an idea, pitch, or brief into a requirements doc.
---

# prd-draft

Turns "the business wants X" into the document that aligns everyone on **what problem, for whom, how we'll know** — before anyone argues about how. The missing link in the pipeline: `brief-intake` (raw mess → brief) → **`prd-draft`** → `user-story-splitter` (stories), `nfr-spec` (quality targets), `success-metrics` (measurement), `design-doc` (the how).

## How to respond

1. **Ingest the idea** — a `brief-intake` output, a pitch paragraph, a meeting note. Ask at most 2 questions, spent on the two highest-leverage unknowns: **evidence** ("what tells us users actually have this problem?") and the **binding constraint** ("fixed deadline, fixed scope, or fixed team?"). Everything else: pick a default, tag it `[assumption]`.

2. **Write the problem statement with zero solution nouns.** It names users, their situation, the pain, and the evidence — and survives the test: *could this paragraph justify a completely different solution than the one everyone has in mind?* ✅ *"Support agents spend ~20 min/ticket reconstructing customer order history across three tools `[reported by support lead]`"* — ❌ *"We need an order-history dashboard"* (that's a solution wearing a problem costume).

3. **Name the users specifically enough to find one.** Primary persona + their job-to-be-done; secondary personas listed but explicitly deprioritized. "All users" is not a persona — if the feature really serves everyone, name who feels the pain *most*.

4. **State goals with a success line each.** Every goal carries one measurable "we'll know it worked when …" sentence — target, timeframe, baseline if known. One line here; the full measurement design (instrumentation, guardrails) is `success-metrics`' job — point the user there.

5. **Write requirements that are testable and solution-free**, each with a MoSCoW priority — and the **Won't-have list is mandatory**: ✅ *"M — Agent sees a customer's orders from all channels in one view, ≤3s after lookup"* — ❌ *"M — Use Redis to cache order data"* (implementation, belongs in `design-doc`) — ❌ *"S — The experience is seamless"* (untestable, belongs nowhere). Requirements describe observable behavior or capability; each one is checkable by a tester or demo.

6. **Make non-goals carry weight — minimum 3.** Non-goals are the section that kills scope creep in review instead of in sprint 4. Each names the thing stakeholders will plausibly ask for, and one line on why it's out: ✅ *"Editing orders from this view — read-only for v1; write paths triple the authz surface (revisit after launch metrics)"*.

7. **List open questions with owners and dates** — the unknowns that block requirement freeze, each assigned to a person/role who can actually answer it. An open question without an owner is a future surprise.

8. **Emit the PRD with [`templates/prd.md`](templates/prd.md)** in one message, sized for a 30-minute read. End with the handoff map: stories → `user-story-splitter`, quality targets → `nfr-spec`, measurement → `success-metrics`, technical approach → `design-doc`.

## Useful references in this skill

- [`templates/prd.md`](templates/prd.md) — the PRD skeleton with the solution-language test and MoSCoW table

## Quality bar

- **The problem statement passes the alternative-solution test.** If only one solution could follow from it, it's a spec, not a problem.
- **Every requirement is verifiable** — a tester can demo it pass/fail. Implementation choices and adjective requirements both fail.
- **Won't-have list is non-empty and specific.** "Out of scope: everything else" is an empty gesture; name the tempting things.
- **Every goal has a success line with a number and a timeframe.** "Improve agent efficiency" is a hope; "median handle time −25% within 60 days of GA" is a goal.
- **Evidence is tagged to its source** — `[reported by X]`, `[data: Y]`, `[assumption]`. A PRD's authority is exactly as good as its weakest untagged claim.
- **It reads in 30 minutes.** Length is a tax on every reviewer; appendices exist for the rest.

## When to use this skill

- ✅ A feature idea needs to become an agreed requirements doc before design starts
- ✅ "Write a PRD for X" / "capture the business requirements for X"
- ✅ A `brief-intake` output is ready to be shaped into the canonical product doc
- ✅ Two teams disagree about what's being built — the PRD is the alignment artifact

## When NOT to use this skill

- ❌ The technical how — architecture, stack, data model → `design-doc`
- ❌ Splitting into sprint-sized work → `user-story-splitter` (after the PRD)
- ❌ Whether to invest at all → `business-case`; the PRD assumes the investment decision is made
- ❌ A tiny change that needs a ticket, not a doc → `user-story-splitter` or `bug-triage`

## Anti-patterns to avoid

- ❌ **Solution-as-problem.** "Problem: we don't have a dashboard." The absence of a solution is never the problem.
- ❌ **Implementation smuggled into requirements.** "Must use Kafka" — the PRD owns *what*; smuggled *hows* pre-empt design without review.
- ❌ **Adjective requirements.** Fast, seamless, intuitive, robust — each one either gets a number or gets cut.
- ❌ **The empty non-goals section.** A PRD that excludes nothing has decided nothing; it's a wish list with a header.
- ❌ **Stakeholder wish-list flattening.** Every request recorded as "Must" because saying Should felt political — MoSCoW with one priority level is no prioritization.
- ❌ **The 40-page PRD.** Completeness theater; nobody reviews page 23, so page 23 ships unreviewed.
