---
name: ai-adoption-rollout
description: Plan the human rollout of an AI tool or workflow to an organisation — sized cohorts, enablement per cohort, named champions, a comms plan that states what will not change, and an adoption gate every wave must pass before the next one opens. Use when a tool has been chosen and the question is how it reaches people without stalling or backlash. Do NOT use to phase a technical cutover (that's migration-plan) or to choose which use case to roll out (that's ai-use-case-triage).
---

# ai-adoption-rollout

The tool is chosen; the risk now is **people**. This plans the human rollout: who gets it when, what they're taught, who they ask, what they're told, and the observable that must hold before the next cohort opens.

Rollouts fail quietly. Licences get assigned, a launch email goes out, usage spikes for a week and decays, and nobody can say which step failed. Every wave here carries a gate so that decay is visible while it's still fixable.

## How to respond

1. **Restate what's being rolled out, to whom, and the adoption outcome.** Not "increase AI usage" — a behaviour: "support agents draft first responses with assistance on the top 3 categories". Usage is a proxy; the behaviour is the goal. Cap clarifying questions at 2.

2. **Design cohorts, smallest first.** Default three waves — **pilot** (5–15 volunteers, highest tolerance) → **early** (one whole team or function, includes sceptics) → **general**. Each cohort names who is in it and *why they're next*: the pilot proves the workflow, the early wave proves it survives people who didn't ask for it. Skipping straight to general is the most common failure and this skill refuses it.

3. **Specify enablement per cohort, not one training deck.** What each cohort must be able to *do* before they're counted as enabled — a 30-minute hands-on with their own real task beats an hour of slides. Name the format, the time cost, and who delivers it. Later cohorts get shorter enablement built from what the pilot actually got stuck on.

4. **Name champions by role, with a time budget.** One per cohort, with hours protected. An unbudgeted champion is a volunteer who quietly stops answering. State what they own: first-line questions, collecting friction, running the office hour.

5. **Write the comms plan — including what will not change.** Three messages: the announcement (what, why, what's in it for the reader), the reassurance (**explicitly: whether this affects headcount, evaluation, or how work is judged**), and the follow-up. Silence on the reassurance point is read as bad news and is the single biggest driver of quiet non-adoption.

6. **Put an adoption gate on every wave.** Observable, with a threshold and a bake time, before the next cohort opens. ✅ "≥60% of the pilot used it on a real task in week 2, and no unresolved 🟥 issue in the friction log — hold 1 week." A gate that is "the pilot went well" is not a gate. Each wave also names its **rollback**: what happens if the gate fails — extend, narrow, or stop.

7. **Name the friction loop.** Where friction is captured, who triages it weekly, and how a fix reaches the next cohort. A rollout with no feedback path teaches the organisation that complaints go nowhere.

## Quality bar

- **Cohorts get smaller-to-larger with a stated reason each**, and the plan refuses a single big-bang wave.
- **Every wave has an adoption gate with an observable, a threshold, and a bake time** — plus a rollback if it fails.
- **The outcome is a behaviour, not a usage number.** Licences activated is not adoption.
- **The comms plan states explicitly what will not change** (headcount, evaluation, how work is judged). Omitting it is a defect, not a tone choice.
- **Champions are roles with protected hours**, never names, and never unbudgeted.
- **Enablement is per cohort and hands-on with the participant's own work** — a single deck for everyone is the failure mode.
- **The friction loop names an owner and a cadence.**

## When to use this skill

- ✅ A tool or AI workflow is chosen and now has to reach real people.
- ✅ A previous rollout decayed after launch and you're planning the retry.
- ✅ Leadership wants a timeline with checkpoints rather than a launch date.

## When NOT to use this skill

- ❌ Phasing a *technical* cutover (schema, API version, datastore) — that's `migration-plan`, which sequences systems, not people.
- ❌ Choosing which use case to roll out — that's [`ai-use-case-triage`](../ai-use-case-triage/SKILL.md).
- ❌ Deciding whether the organisation is ready at all — that's [`ai-readiness-assessment`](../ai-readiness-assessment/SKILL.md).
- ❌ Writing the rules for what may be put into the tool — that's [`ai-usage-policy`](../ai-usage-policy/SKILL.md).
- ❌ Reporting on adoption that already happened — that's `ai-usage-report`.

## Anti-patterns to avoid

- ❌ **Big-bang rollout.** Everyone at once means no cohort to learn from and no way to stop. The gate structure exists to prevent exactly this.
- ❌ **Counting licences as adoption.** Seats assigned, logins, "activated users" — all measure procurement, not behaviour change.
- ❌ **A launch email as the comms plan.** One announcement with no reassurance and no follow-up is how a rollout gets read as a threat.
- ❌ **Champions with no time.** Naming an enthusiastic person and adding nothing to their calendar is delegation of blame.
- ❌ **Training everyone identically.** The pilot's stumbling blocks should shorten the next cohort's enablement; if the deck never changes, nobody was listening.
- ❌ **A gate with no rollback.** "Proceed if it goes well" is not a decision rule — say what happens when it doesn't.

**Non-interactive:** with no user to ask, derive cohorts from the stated org size and tag them `[assumption]`. If the input names no tool or workflow to roll out — only a wish to "drive AI adoption" — emit `BLOCKED: need the specific tool or workflow being rolled out and the population it reaches`.
