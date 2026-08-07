---
name: agent-adoption-stage
description: Place an engineering team on the agentic-coding adoption ladder (0 gated → 4 intent-steered) using observables like agents-in-flight per engineer and who writes the code, name the one bottleneck gating the next step, prescribe the single next unlock, and state which current guardrail must change. Use when a leader asks "how far along are we with coding agents", "why has our AI adoption plateaued", or "what do we do next to get more out of this". Do NOT use to assess organisational preconditions like data, policy, and culture (that's ai-readiness-assessment) or to plan a tool's human rollout (that's ai-adoption-rollout).
---

# agent-adoption-stage

Answer one question honestly: **which rung is this team actually on, and what is the single next thing that moves them up?** Not a scorecard, not a tool list — a placement backed by observables, the bottleneck that gates the next step, and one unlock.

Adapted from Boris Cherny's *Steps of AI Adoption* (2026-07-16). The stage names and the bottleneck-shift are his; the guardrail changes and the routing here are skilldrop's, and everything is stated as a **capability** rather than a product so it stays true across tools and across years.

The load-bearing idea: **the bottleneck moves.** Each stage is limited by something different, so a fix that unlocked the last step does nothing for the next one. Diagnosing the *current* bottleneck is the whole job; the stage number is just its index.

## The ladder

| Stage | Shape | Observable | The bottleneck |
|---|---|---|---|
| **0 · Gated** | no real access | tools unapproved, gateways slow, no path to run outputs | approval process — a legacy security posture optimising cost-per-token instead of outcomes |
| **1 · Assisted** | you + one agent | **~1 agent**, synchronous, you read nearly every change | **your attention.** Low trust and no self-verification, so you watch instead of moving on |
| **2 · Parallel** | you orchestrate | **~5–10 agents**, isolated checkouts, agent checks its own work first | **review throughput.** You're checking six streams instead of writing one |
| **3 · Supervised autonomy** | manager of managers | **~100**, agent writes nearly all code, agents start agents | **trust in the loop**, and token efficiency as volume climbs |
| **4 · Intent-steered** | steer by intent | **~1000+**, loop closed, monitor by exception | **finding and automating the work**, with the right guardrail per work type |

## How to respond

1. **Place the team on exactly one stage, from observables.** Ask for (or extract) three things: how many agents a typical engineer has in flight, who writes most of the code now, and what gets reviewed — every diff, final diffs, or exceptions. Quote the evidence. **A range is a refusal** — pick the stage the team is *operating at*, not the best day it ever had. Cap clarifying questions at 2.

2. **Discount aspiration.** A team that bought licences for 200 people and has three power users is at stage 1 with an outlier, not stage 2. Place on the median engineer, and say so when the distribution is lopsided — the spread is itself a finding.

3. **Name the current bottleneck in one sentence,** and check it against the table. If the team's stated pain doesn't match the stage's bottleneck, that mismatch is the most interesting thing in the assessment — surface it. ("You say review is the constraint, but engineers still run one agent at a time; the constraint is trust, not throughput.")

4. **Prescribe exactly one unlock.** The next step, never a backlog of ten. The transitions:
   - **0 → 1:** an approved path to run agents and land their output. Executive alignment, not tooling.
   - **1 → 2:** **a self-verification loop the engineer trusts** — tests, build, lint, typecheck running *before* they look — plus more than one agent at a time and pre-approved safe commands so permission prompts stop blocking.
   - **2 → 3:** context and delegation — let agents read the code, docs and discussions; automate review so it isn't the queue; break work into loops and routines; let agents start agents.
   - **3 → 4:** scaled automation of domain-specific work (migrations, fuzzing, remediation) with per-work-type guardrails.

5. **State which guardrail must change**, not just what to add. Guardrails are stage-appropriate, and carrying the old one forward is what stalls teams: reading every diff is right at stage 1 and *arithmetically impossible* at stage 3, where the control moves to the loop (automated review, sandboxing, isolation) and humans review by exception. Name the one to retire and the one to introduce.

6. **Route the unlock to something concrete.** Each unlock has an implementation:

   | Unlock | Where it's implemented |
   |---|---|
   | a trusted self-verification loop | [`pre-merge-review`](../pre-merge-review/SKILL.md) — a mechanical gate whose exit code decides, plus the reviewer panel |
   | automated review that isn't the queue | the reviewer panel (`devils-advocate`, `security-reviewer`, `code-quality`) |
   | loops and routines | [`agent-loop-design`](../agent-loop-design/SKILL.md) — generate→verify→gate with exit criteria and a cap |
   | parallel agents without collision | [`subagent-design`](../subagent-design/SKILL.md) — topology, isolation, typed contracts |
   | token efficiency as volume climbs | [`agent-budget`](../agent-budget/SKILL.md) + a provider-neutral model tier per task |
   | encoding standards so agents inherit them | [`agents-md-generator`](../agents-md-generator/SKILL.md) and skills themselves |
   | guardrails for autonomous work | [`agent-threat-model`](../agent-threat-model/SKILL.md) |

7. **End with the re-measure date and what would prove the unlock landed.** An observable: "median agents-in-flight ≥ 3 and engineers stop reading intermediate diffs, in 6 weeks."

## Quality bar

- **Exactly one stage, cited to observables.** No ranges, no "between 2 and 3" — and never a placement asserted from ambition or licence count.
- **Placement is on the median engineer**, with the distribution named when it's lopsided.
- **Exactly one unlock.** A list of ten is a backlog, and it guarantees none of them happens.
- **The bottleneck is the one gating the *next* step**, not a general complaint about AI.
- **A guardrail to retire is named**, not only one to add — stage-appropriateness cuts both ways.
- **Every unlock routes to a concrete implementation**, never to a product name.
- **Vendor-neutral throughout.** Capabilities, not SKUs; a skill that names this quarter's products is wrong by next quarter.
- **The source framework is credited.**

## When to use this skill

- ✅ "How far along are we with coding agents, really?"
- ✅ Adoption plateaued and nobody can name why.
- ✅ A leader wants to scale agent usage and needs to know whether the loop can carry it yet.
- ✅ Re-measuring a quarter after a previous placement.

## When NOT to use this skill

- ❌ Assessing organisational preconditions — data, policy ownership, incentives — that's [`ai-readiness-assessment`](../ai-readiness-assessment/SKILL.md), a different axis (a team can be governance-ready and stuck at stage 1).
- ❌ Planning how a tool reaches people — cohorts, enablement, comms — that's [`ai-adoption-rollout`](../ai-adoption-rollout/SKILL.md).
- ❌ Choosing which use cases to build — that's [`ai-use-case-triage`](../ai-use-case-triage/SKILL.md).
- ❌ Reporting measured usage from telemetry — that's [`ai-usage-report`](../ai-usage-report/SKILL.md).
- ❌ Designing one specific loop or fleet — that's `agent-loop-design` / `subagent-design`, which this skill routes *to*.

## Anti-patterns to avoid

- ❌ **Scaling agent count before the loop has earned trust.** The named trap of stage 2→3: more agents on an unverified loop multiplies review burden instead of output. Trust first, count second.
- ❌ **A stage claimed from ambition.** Licences bought, a mandate announced, or one enthusiastic staff engineer are not a stage. Median engineer, observable behaviour.
- ❌ **Carrying stage-1 guardrails upward.** "Read every diff" doesn't scale to ten streams and is arithmetically impossible at a hundred; insisting on it is what caps a team at stage 1 while everyone blames the model.
- ❌ **Answering with a product list.** Tools don't move a team up a rung — a trusted verification loop does. Name the capability and the loop change.
- ❌ **Prescribing the whole ladder.** Handing someone stages 2, 3 and 4 at once guarantees stage 1 forever.
- ❌ **Treating the stage as a status symbol.** Stage 4 is not better for a team whose work doesn't need it; the right stage is the one the work and the trust support.

**Non-interactive:** with no user to ask, infer the stage from whatever observables the input contains and tag the placement `[assumption]`, naming what to confirm. If the input has no observable at all — no agent counts, no review posture, no statement of who writes the code — emit `BLOCKED: need at least one observable (agents in flight per engineer, who writes most of the code, or what gets reviewed)` rather than guessing a stage, because a wrong placement prescribes the wrong unlock.
