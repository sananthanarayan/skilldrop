---
name: ai-readiness-assessment
description: Score an organisation's or team's readiness to adopt AI tooling across six gating dimensions — data, tooling, skills, governance, process, and culture — with an evidence line per score and the blocking gaps ranked by what stops adoption first. Use when the user asks "are we ready for AI", wants an AI maturity or readiness baseline, or needs to know what to fix before rolling tools out. Do NOT use to pick which use cases to build (that's ai-use-case-triage) or to plan the rollout itself (that's ai-adoption-rollout).
---

# ai-readiness-assessment

Produce a **baseline a leadership team can act on**: where the organisation actually stands on the six things that gate AI adoption, what the evidence is for each score, and which gaps block adoption *first*. The output is a scored table plus a ranked gap list — not a maturity label and not a slide.

Readiness assessments fail in one of two ways: a number with no evidence behind it, or a diagnosis with no next action. This skill refuses both.

## How to respond

1. **Establish scope and the decision it feeds.** Whose readiness — one team, a function, the whole company? And what happens with the answer (a go/no-go, a budget request, a sequencing decision)? Scope changes what counts as evidence. Cap clarifying questions at 2.

2. **Score the six dimensions.** These are fixed — do not invent new ones for a single engagement, and do not drop one because it's awkward to assess. Score each **0–4** (0 absent · 1 ad hoc · 2 repeatable · 3 managed · 4 optimised):

   | Dimension | The question it answers |
   |---|---|
   | **Data** | Is the material these tools need reachable, current, and permitted to be used? |
   | **Tooling** | Are licences, access, and environments actually in people's hands? |
   | **Skills** | Can people write a decent prompt, judge an output, and know when not to trust it? |
   | **Governance** | Is there a rule for what may be put in, and a named owner for it? |
   | **Process** | Does the workflow have a place for a machine draft plus a human review gate? |
   | **Culture** | Is the incentive to use it, or to hide that it was used? |

3. **Attach evidence to every score.** One line naming what you observed — a system, a document, a stated practice, a number. A score with no evidence line is deleted, not softened. Where the input doesn't support a score, emit `[insufficient evidence: <what to collect>]` rather than guessing a middle number.

4. **Rank the gaps by what blocks first, not by what scores lowest.** A 1 in Governance that blocks every use case outranks a 0 in Culture that blocks nothing yet. Name the dependency: "Skills cannot move until Tooling ≥ 2 — people can't practise on access they don't have."

5. **Give each gap a first action and an owner role.** Concrete and small enough to start this quarter. ❌ "Improve data governance." ✅ "Name a data owner for the three systems in scope and publish an allowed-use tier for each — legal + platform lead, 2 weeks."

6. **State the overall posture in one sentence, and what would change it.** ✅ "Ready for a bounded pilot in engineering; not ready for company-wide rollout until Governance reaches 2." Never a bare maturity label.

## Quality bar

- **Every score carries an evidence line.** A number with nothing behind it is the failure mode this skill exists to prevent — cut it or mark it `[insufficient evidence]`.
- **All six dimensions appear**, including the ones the input is thin on. Silence on a dimension reads as a pass, and that's how readiness reports mislead.
- **Gaps are ranked by blocking order, not by score.** The lowest number is not automatically the first problem, and the plan must say why.
- **Every gap has a first action and an owner role** — a role, never a person's name, so the assessment doesn't go stale when someone changes teams.
- **The posture sentence takes a position** and names the condition that would change it. "It depends" is a refusal to do the job.
- **No invented facts.** Where the input is silent, say so; a fabricated observation is worse than an admitted gap.

## When to use this skill

- ✅ "Are we ready to roll out AI tooling?" — before committing budget or a timeline.
- ✅ Establishing a baseline to re-measure against in two quarters.
- ✅ A leadership team disagrees about whether the blocker is tools, skills, or policy.

## When NOT to use this skill

- ❌ Choosing *which* workflows to automate — that's [`ai-use-case-triage`](../ai-use-case-triage/SKILL.md).
- ❌ Planning the rollout once you've decided to go — that's [`ai-adoption-rollout`](../ai-adoption-rollout/SKILL.md).
- ❌ Writing the rules for what people may put into a tool — that's [`ai-usage-policy`](../ai-usage-policy/SKILL.md).
- ❌ A market or competitive question ("should we enter this space?") — that's `strategy-analysis`.
- ❌ Measuring adoption that has already happened — that's `ai-usage-report`.
- ❌ **Assessing how far an engineering team's agent practice has actually got** — agents in flight, who writes the code, what still gets reviewed — that's [`agent-adoption-stage`](../agent-adoption-stage/SKILL.md). It's the orthogonal axis: this skill scores whether the *organisation* can adopt at all; that one scores how far the *practice* has got. A team can be governance-ready and stuck at stage 1, or running ten agents with no policy at all — run both when the answers disagree.

## Anti-patterns to avoid

- ❌ **A maturity label as the deliverable.** "You are Level 2 of 5" tells a leader nothing they can fund. The ranked gap list is the product; the score is just its index.
- ❌ **Scoring what's easy to score.** Tooling is countable, Culture is not — and a report that goes deep on licences and hand-waves incentives has measured the wrong thing.
- ❌ **Middle scores as a hedge.** A 2 everywhere means the assessment refused to commit. If the evidence is thin, say `[insufficient evidence]` and name what to collect.
- ❌ **Gaps with no owner.** An unowned action is a wish. Roles, not names.
- ❌ **Recommending tools.** This assesses readiness; vendor selection is a different decision (`tech-comparison-matrix`) and mixing them lets a vendor pitch masquerade as a diagnosis.

**Non-interactive:** with no user to ask, derive the scope from the input and tag it `[assumption]`. If the input contains no observable evidence for any dimension — a request with no organisational context — emit `BLOCKED: need observable context (systems, current practice, or stated policy) for at least three dimensions` rather than scoring from imagination.
