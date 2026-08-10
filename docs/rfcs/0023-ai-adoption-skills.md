---
rfc: 0023
title: AI adoption skills — readiness, use-case triage, rollout, usage policy
status: implemented
date: 2026-08-07
author: sananthanarayan
---

# RFC-0023: AI adoption skills — readiness, use-case triage, rollout, usage policy

## Problem / use case

skilldrop's `ai-engineering` pack is strong on **building** AI systems — `agent-loop-design`,
`subagent-design`, `agent-budget`, `agent-threat-model`, `llm-eval-harness` — and on measuring usage
after the fact (`ai-usage-report`). It has nothing for the stage *before* any of that: an organisation
deciding **whether, where, and how** to adopt AI at all.

That's a real gap for skilldrop's actual audience. The people who reach for `prfaq`, `okr-cascade`
and `business-case` are the same people asked "are we ready for this?", "which workflows should we
automate first?", "how do we roll it out without a backlash?" and "what are people allowed to put
into these tools?" Today they get nothing, or they bend a generic strategy skill into a shape it
wasn't built for.

Four artifacts, none of which any existing skill produces:

1. **Readiness assessment** — a scored baseline across the dimensions that actually gate adoption.
2. **Use-case triage** — a ranked portfolio of candidate use cases, with an explicit not-yet list.
3. **Adoption rollout** — the *human* rollout: cohorts, enablement, champions, comms, gates.
4. **Usage policy** — the org-level acceptable-use policy: what may be put in, what needs review.

## Fit check

For each, the four criteria from **Authoring a new skill**:

- **Concrete artifact:** a scored readiness table with ranked gaps · a prioritised use-case portfolio
  with a first slice · a phased rollout plan with cohorts and adoption gates · a policy document with
  data tiers and a review matrix. All four are documents a reader acts on, not advice.
- **Portable:** pure prose skills, no scripts, no deps, no env. Plain folder copy, every tool.
- **Opinionated:** each makes decisions rather than asking. Readiness scores against a fixed
  dimension set and refuses an unevidenced score. Triage ranks on value × feasibility × risk and
  forces a not-yet list. Rollout requires a cohort gate before widening. Policy defaults to
  three data tiers and requires a named owner per rule.
- **Category:** extends **AI adoption & observability** (README §8) — which currently holds only
  `ai-usage-report` and `llm-eval-harness`, both post-adoption. These are its front half.

They do not duplicate existing skills, and each states its boundary in `When NOT to use`:
`strategy-analysis` runs a general framework (SWOT/Five Forces) on a market question, not an AI
capability baseline; `business-case` prices *one* decision rather than ranking a portfolio;
`migration-plan` phases a *technical* cutover (expand→migrate→contract) while `ai-adoption-rollout`
phases *people*; `agents-md-generator` writes a repo's agent-tooling policy while `ai-usage-policy`
writes the organisation's human acceptable-use policy; `agent-threat-model` analyses one agent's
capability surface rather than setting org-wide rules.

## Proposal

Four new skills, all `standard` tier (rubric-bounded generation, not adversarial judgment), all in
the `ai-engineering` pack; `ai-use-case-triage` additionally joins `product-manager`, where the
"what should we build with this?" question actually lands.

| Skill | Produces | Refuses |
|---|---|---|
| `ai-readiness-assessment` | scored baseline across 6 dimensions + ranked blocking gaps | an unevidenced score; a maturity label with no next action |
| `ai-use-case-triage` | ranked portfolio (value × feasibility × risk) + first slice + not-yet list | a portfolio with no rejections; ranking without a stated weight |
| `ai-adoption-rollout` | cohort-phased rollout with enablement, comms, and adoption gates | widening a cohort without a passed gate; a plan with no rollback |
| `ai-usage-policy` | acceptable-use policy: data tiers, permitted/prohibited uses, review matrix | a rule with no owner; a prohibition with no permitted alternative |

Each ships the mandatory `Quality bar` + `Anti-patterns to avoid`, a non-interactive line, and
`evals/` (required for new skills) — with `should_trigger: false` rows pointing at the siblings above,
since these four collide with each other and with `strategy-analysis` / `business-case` /
`migration-plan` by design.

## Alternatives considered

- **A fifth skill for AI ROI / value measurement.** **Rejected as duplicative** — the fit check's own
  "does it duplicate an existing skill?" test fails it. Pricing an AI investment is `business-case`
  (Option 0, three cost layers, confidence-tagged benefits); defining what success looks like and the
  decision rule is `success-metrics`; reporting actual usage and effectiveness is `ai-usage-report`.
  A separate ROI skill would restate all three with an "AI" prefix. The composition already works;
  a wrapper would be filler.
- **One combined `ai-adoption-plan` skill.** Rejected — the four artifacts have different audiences
  (exec, product, enablement lead, legal/security) and different lifetimes. A merged skill would be a
  flooding prompt, which `anti-patterns` explicitly forbids.
- **Extending `strategy-analysis` with an AI mode.** Rejected — it is a framework runner (SWOT / Five
  Forces / PESTLE) with its own quality bar; bolting an unrelated assessment into it dilutes both.

## Decision

Accepted and implemented: four skills added to `skills/`, registered in `model-routing.json`,
`packs.json`, and the README (count 51 → 55), each with `evals/`. The AI-ROI skill is declined as
duplicative and recorded above so the idea leaves a trace and isn't re-litigated.
