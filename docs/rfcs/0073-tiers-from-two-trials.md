---
rfc: 0073
title: Skill tiers set from two trials
status: implemented
date: 2026-11-04
author: sanjay-ananth
---

# RFC-0073: Skill tiers set from two trials

## Problem / use case

Each skill's tier (light, standard or heavy) was set by judgment when it was written. The
first tier trial (18 October) suggested a cheaper model was enough for most skills. No tier
moved, because one trial with two evals per skill is an anecdote. The roadmap set the next
step: run light and heavy a second time on the same evals, then set each tier from the
numbers.

## Fit check

No skill instructions change. This moves the `model.tier` in each affected skill's
`manifest.json` and in `model-routing.json`, which must agree (`validate.py` checks), and
bumps each skill's patch version so `skilldrop update` carries the new tier.

## Proposal

**The data.** The 216 held-out evals of the first tier trial, run a second time on light
(`claude-haiku-5-5`) and heavy (`claude-opus-5-5`), with the same judges:
- [`tier-light-trial-2.json`](../benchmarks/tier-light-trial-2.json), $28.63;
- [`tier-heavy-trial-2.json`](../benchmarks/tier-heavy-trial-2.json), $95.21.

Standard is the Sonnet 5.5 run on the same evals
([`standard-sonnet-5-5.json`](../benchmarks/standard-sonnet-5-5.json)). Two skills retired by
RFC-0072 are left out.

**The rule.** The measure is the share of a skill's checks met with the skill, the measure the
benchmark's routing check uses.
- **Down a tier:** when the cheaper model meets within 5 points of the best tier in both
  trials.
- **Up a tier:** when the dearer model is more than 5 points ahead of the others in both
  trials.
- **One step at a time,** and heavy never moves down. That is `model-routing.json`'s rule,
  because a heavy skill's value is the case a fast pass misses, which two evals rarely
  contain.
- **A move up to heavy needs the skill's `examples/` oracle** (RFC-0016). A skill without one
  stays on standard until it has one.

**The moves (31).** Checks met with the skill, light / standard / heavy, in trial 1 and trial 2:

| Skill | From | To | Trial 1 | Trial 2 |
|---|---|---|---|---|
| `md-to-docx` | standard | heavy | 71%/64%/79% | 79%/64%/93% |
| `user-journey-map` | standard | heavy | 67%/75%/83% | 75%/75%/83% |
| `agent-adoption-stage` | standard | light | 79%/82%/79% | 86%/82%/79% |
| `ai-adoption-rollout` | standard | light | 79%/75%/64% | 71%/75%/64% |
| `ai-use-case-triage` | standard | light | 83%/81%/85% | 92%/81%/92% |
| `api-contract-draft` | standard | light | 76%/69%/69% | 92%/69%/76% |
| `application-form-answers` | standard | light | 88%/88%/81% | 94%/88%/81% |
| `architecture-diagrams` | standard | light | 93%/93%/93% | 100%/93%/93% |
| `cover-letter` | standard | light | 100%/100%/100% | 100%/100%/100% |
| `design-doc` | standard | light | 88%/92%/91% | 88%/92%/91% |
| `feature-implement-loop` | standard | light | 85%/85%/76% | 85%/85%/85% |
| `figma-diagrams` | standard | light | 92%/92%/75% | 92%/92%/92% |
| `incident-comms` | standard | light | 93%/85%/92% | 100%/85%/93% |
| `llm-eval-harness` | standard | light | 71%/71%/71% | 71%/71%/71% |
| `output-hygiene` | standard | light | 100%/92%/100% | 100%/92%/92% |
| `postmortem-generator` | standard | light | 93%/92%/90% | 91%/92%/87% |
| `pr-description-writer` | standard | light | 85%/85%/77% | 85%/85%/85% |
| `pre-merge-review` | standard | light | 93%/86%/93% | 93%/86%/93% |
| `release-notes` | standard | light | 96%/91%/100% | 96%/91%/98% |
| `research-plan` | standard | light | 79%/79%/79% | 79%/79%/79% |
| `resume-tailor` | standard | light | 100%/100%/100% | 100%/100%/100% |
| `service-blueprint` | standard | light | 100%/92%/85% | 92%/92%/92% |
| `skill-author` | standard | light | 100%/93%/100% | 93%/93%/92% |
| `slide-outliner` | standard | light | 86%/83%/83% | 90%/83%/93% |
| `source-synthesis` | standard | light | 83%/76%/85% | 78%/76%/82% |
| `team-status-report` | standard | light | 93%/93%/93% | 93%/93%/93% |
| `terraform-module` | standard | light | 100%/92%/83% | 100%/92%/100% |
| `test-plan-generator` | standard | light | 76%/76%/61% | 92%/76%/54% |
| `tool-use-schema-writer` | standard | light | 94%/96%/97% | 94%/96%/97% |
| `ux-writing` | standard | light | 92%/83%/75% | 92%/83%/83% |
| `decision-log` | light | standard | 79%/79%/86% | 61%/79%/76% |

**Measured heavier but not moved yet:** `bug-triage`, `prd-draft`, `prompt-caching-advisor`
and `subagent-design`. Heavy was more than 5 points ahead in both trials, but none ships an
`examples/` oracle. Each moves when it has one.

**Light was enough, heavy kept:** `accessibility-audit`, `doc-critique`, `skill-review` and
`strategy-analysis`.

## Alternatives considered

- **Move on the blind preference instead.** The judges compare a skill with the plain agent on
  the same model, not one model with another. The tier is a question about models.
- **Wait for more evals per skill.** Two trials that agree on the same evals is the bar the
  roadmap set. A wrong move is cheap to undo: the next trial can move a skill back.
- **Move heavy skills down too.** Two evals rarely hold the hard case a heavy skill exists for.
  The rule stays, and these four are recorded.

## Decision

Implemented on branch `sanjay-ananth/measure-loops-and-decide`.
