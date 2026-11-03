---
rfc: 0069
title: Adopt, ship-agent, provision and clarify loops
status: implemented
date: 2026-11-03
author: sanjay-ananth
---

# RFC-0069: Adopt, ship-agent, provision and clarify loops

## Problem / use case

Ten of the nineteen packs had no loop. Four of them hold skills that are only useful in order,
and the tutorials already walk the order by hand.
- **`ai-engineering`** is the largest pack and had none. A usage policy written before anyone
  picks a first use case covers every tool and every kind of data, and nobody reads the part that matters.
  An agent threat-modelled before its design exists inventories capabilities nobody chose.
- **`infra-as-code`:** a module with secure defaults can still produce a plan that replaces a
  database, and a plan reviewed on Tuesday is not the one applied on Thursday.
- **`experience-design`:** a page rewritten to a lower reading grade can leave every call it
  was meant to stop, when the cause is a wait backstage.

## Fit check

A structural change. It adds loops over skills that already exist (golden rule 7: a loop orders
skills, a skill never invokes one).
- Each loop lives in one pack that, with `core`, holds every skill it runs.
- None goes in `model-routing.json`.
- Gate ids follow RFC-0044. The loops outside the lifecycle take G11 to G14.

## Proposal

| Loop | Pack | Stages | Gates |
|---|---|---|---|
| `adopt` | `ai-engineering` | `triage` → `readiness` → `policy` → `rollout` → `sign-off` (`doc-critique`) | **G11** review, readiness against the slice; **G11.1** human, the sponsor |
| `ship-agent` | `ai-engineering` | `design` (`agent-loop-design`, `subagent-design`) → `budget` → `threat` → `evals` → `launch` (`agent-config-review`) | **G12** review, every trifecta path fixed in the architecture; **G12.1** human, the owner |
| `provision` | `infra-as-code` | `module` → `plan` → `apply` (`terraform-plan-review`) | **G13** review, the real plan against the scope; **G13.1** human, the plan applied is the plan reviewed |
| `clarify` | `experience-design` | `page` (`content-design`) → `strings` (`ux-writing`) → `blueprint` (`service-blueprint`) | **G14** review, the words reach the complaints' causes |

The rules each loop adds, which no single skill can enforce:
- **adopt:** readiness is scored against the first slice, so a gap blocks only what needs it.
  `REVISE` changes the slice, never the scores. The pilot is the slice's users, and its gate
  is the observable triage named.
- **ship-agent:** every threat-model attack becomes an eval case in the critical subset. The
  launch review checks the built configuration against what the threat model allowed. The
  loop stops while the team builds, and resumes at `launch`.
- **provision:** the scope is written as resource addresses before any plan exists. Only a
  saved planfile counts, and G13.1 checks its hash. The loop never runs `apply`.
- **clarify:** the complaints are written down first, and the blueprint marks each one as
  reached by the page, reached by the strings, or caused backstage. `RECONSIDER` sends a
  backstage cause to product.

Not one of these loops is measured yet. [RFC-0070](0070-benchmarking-loops.md) adds the arm
that can measure them. Each loop ships with author evals, and held-out evals written blind
from its description alone.

## Alternatives considered

- **More pack journeys.** A journey has no gate and no cap. Every failure above happens
  between two skills, and a journey has nowhere to stop it.
- **A loop for every pack without one.** `api-builder`, `converters`, `design`, `frontend`,
  `skill-engineering`, `stakeholder-comms` and `trackers` hold skills that each work alone.
  Ordering them would add stages nobody needs.
- **`agent-adoption-stage` in `adopt`.** It places an engineering team on the coding-agent
  ladder, a different question from "where does this organisation start".
- **A figures gate in `ship-a-draft` (G5.1).** It was built with this RFC, on `figure-check`
  ([RFC-0071](0071-figure-check.md)). That skill lost its admission twice, so the gate went
  with it.

## Decision

Implemented on branch `sanjay-ananth/loops-bench-claims`.
