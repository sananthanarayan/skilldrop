---
rfc: 0024
title: agent-adoption-stage — position a team on the agentic-coding ladder
status: implemented
date: 2026-08-07
author: sananthanarayan
---

# RFC-0024: `agent-adoption-stage` — position a team on the agentic-coding ladder

## Problem / use case

RFC-0023 added four AI-adoption skills that assess **organisational preconditions** — data,
governance, culture, policy, use-case portfolio, human rollout. None of them answers the question an
engineering leader actually asks once tools are in people's hands: **"how far along is our
engineering practice, and what is the single next thing that unlocks the next level?"**

Boris Cherny's *Steps of AI Adoption* (2026-07-16) frames this well, and its framing is the part
skilldrop is missing:

- **A stage ladder with an observable** — 0 Gated → 1 Assisted → 2 Parallel → 3 Supervised autonomy
  → 4 AI-native, indexed by agents-in-flight per engineer (~1 / ~10 / ~100 / ~1000+) and by who
  writes the code.
- **A bottleneck that *shifts* per stage** — your attention → review throughput → trust in the loop →
  identifying work to automate. This is the real insight; a static maturity rubric misses it.
- **Named transitions**, one per step boundary.
- **Stage-appropriate guardrails** — "read every diff" is correct at stage 1 and *impossible* at 3.

The striking part on inspection: **skilldrop already ships the rungs of this ladder** —
`pre-merge-review` + `gate.py` is the trusted self-verification loop that unblocks 1→2, the reviewer
panel is the automated review, `subagent-design` is parallel isolation, `agent-loop-design` is loops
and routines, `agent-budget` + `model-routing.json` is token control, `agents-md-generator` encodes
standards. What's missing is the **map** that says which rung you're on and which one is next.

## Fit check

- **Concrete artifact:** a stage placement with cited observables, the named current bottleneck, one
  next unlock, the stage-appropriate guardrail changes, and a routing table to the skills that
  implement the unlock. A document a leader acts on.
- **Portable:** prose only, no scripts, no deps.
- **Opinionated:** forces exactly *one* stage (no ranges), forces exactly *one* next unlock (not a
  backlog), refuses stage-skipping, and refuses a placement asserted from ambition rather than
  observables.
- **Category:** AI adoption & observability, alongside RFC-0023's four.

**Boundary against `ai-readiness-assessment` (the duplication risk):** they score orthogonal axes.
Readiness scores *organisational preconditions* — can we adopt at all (data reachable, policy owned,
incentives aligned). This scores *engineering practice maturity* — how far the loop has actually got.
A team can be governance-ready and stuck at stage 1, or running ten agents with no policy at all.
Both skills state the boundary in `When NOT to use`, and `ai-readiness-assessment` gains an explicit
cross-reference so someone who installs only one is told the other axis exists.

## Proposal

One skill, `agent-adoption-stage` (standard tier, `ai-engineering` pack). Two adaptations that the
source framework does not have and skilldrop requires:

1. **Vendor-neutral.** The source's "products that help" columns are single-vendor. skilldrop's
   whole routing layer is provider-neutral by design (`model-routing.json` never names a vendor model
   in a skill). So the skill describes **capabilities** — "a blocking self-verification gate",
   "worktree-isolated parallel agents", "automated review on by default" — never product names. This
   also keeps it true a year from now.
2. **Attribution.** The stage model is someone else's published framework; the skill cites Boris
   Cherny's *Steps of AI Adoption* rather than absorbing it silently.

The skill's routing table is the reason it earns its place: each unlock points at the skilldrop skill
that implements it, which makes the existing catalogue more useful rather than adding a parallel one.

Anti-patterns it bans: claiming a stage from ambition; scaling agent count before the verification
loop is trusted (the source's own named trap); carrying stage-1 guardrails into stage 2+; answering
with a product list instead of a loop change.

## Alternatives considered

- **Extend `ai-readiness-assessment` with the ladder.** Rejected — different axis, different audience
  (engineering leader vs. exec/governance), and merging them produces the flooding prompt the
  anti-pattern catalogue forbids. The cross-reference solves discoverability without the merge.
- **A second skill for the transitions** (a "stage N→N+1 playbook"). Rejected as filler — the
  transition *is* the unlock section of this skill, and the implementation detail already lives in
  `agent-loop-design` / `subagent-design` / `pre-merge-review`.
- **Copy the source's product columns verbatim.** Rejected — breaks provider neutrality and dates the
  skill to one vendor's current SKU list.
- **Do nothing (it's covered).** Rejected — nothing in skilldrop positions a team on a stage or names
  a shifting bottleneck; the closest skill scores a different axis.

## Decision

Accepted and implemented: `skills/agent-adoption-stage/` with evals, registered in
`model-routing.json`, `packs.json` (`ai-engineering`), and the README (55 → 56).
`ai-readiness-assessment` gains a cross-reference so the two axes stay distinct.
