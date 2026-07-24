---
rfc: 0005
title: Agent-engineering skills — loop design, subagent orchestration, agent budgets
status: implemented
date: 2026-07-24
author: sananthanarayan
---

# RFC-0005: Agent-engineering skills — loop design, subagent orchestration, agent budgets

## Problem / use case

Teams are moving from prompting agents to *designing the systems agents run in* — supervised loops, subagent fan-outs, and the spend that governs both (agent-ready-repo's work-loop/discovery-loop territory). skilldrop has one worked example (`feature-implement-loop` *is* a supervised loop) but no skill that helps a user design their own loop, decompose work across subagents, or budget the tokens those designs burn. Budgets are the connective tissue: an unbudgeted multi-agent loop is a runaway-cost incident wearing an architecture diagram.

## Fit check

Three new skills — concrete artifacts (a loop spec, an orchestration plan with role cards, a budget spec), portable (pure markdown), opinionated (hard iteration caps, verifier≠generator, cheapest-adequate-tier). Category: new README section **Agent engineering**; existing skills that also fit: `feature-implement-loop`, `llm-eval-harness`.

## Proposal

- **`agent-loop-design`** (standard): design a supervised agent loop — trigger, generate→verify→gate states, observable exit criteria, hard revision cap, human gates at irreversible steps, failure routes, per-run budget line. Related: `feature-implement-loop` (the in-repo worked example), `subagent-design`, `agent-budget`, `llm-eval-harness`.
- **`subagent-design`** (standard): decompose a task into orchestrator + subagents — one-mission role cards with typed output contracts, topology choice (pipeline / parallel / judge panel) with the reason, context-isolation rationale, and a verification stage that is never the generator. Related: `agent-loop-design`, `agent-budget`, `council-review` (the judge-panel precedent), `devils-advocate` (the adversarial-verifier precedent), `feature-implement-loop`.
- **`agent-budget`** (standard): the spend spec for an agentic workflow — per-stage tier (reusing the repo's light/standard/heavy abstraction), token cap and hard abort rule per stage, graceful-degradation order, and cost-per-outcome as the governing metric. Related: `agent-loop-design`, `subagent-design`, `capacity-cost-model` (the infra-cost sibling), `llm-eval-harness`.

All three join the `ai-engineering` pack (renamed scope: building and running AI/agentic systems), ship with evals, and get `model-routing.json` entries.

## Alternatives considered

- **One mega-skill ("agentic-systems-design"):** rejected — loops, orchestration, and budgets have different triggers and different readers; a mega-skill would ask five questions to find out which third of itself to run.
- **Fold budgeting into the loop skill as a section:** rejected — budgets also govern non-loop fan-outs, and the user asking "what will this cost" often isn't the loop's designer.

## Decision

Implemented as proposed; skills live-tested via their evals before merge.
