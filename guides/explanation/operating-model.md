---
title: Operating model
summary: Know which stage your work is in, which loop or skills and pack help there, and where the agent stops for your decision.
kind: explanation
---

# Operating model

Every piece of work moves through five stages: find the problem, decide how to build it, build it, ship it, and run it. Skills do the work inside each stage. One stage, shipping, has a loop, which orders those skills and ends at a gate that decides whether the work moves on. The other four use their skills in order, because on held-out evals that did better than a loop ([RFC-0074](../../docs/rfcs/0074-loops-measured-four-retired.md), [RFC-0085](../../docs/rfcs/0085-build-retired-design-kept.md), [RFC-0086](../../docs/rfcs/0086-design-retired.md)).

[![Five stages on a rail, top to bottom. Stage 1, find the problem, in the product-manager pack, uses its skills in order with no loop. Stage 2, decide how to build it, in the solution-architect pack, uses its skills in order with no loop. Stage 3, build, in the dev-team pack, uses its skills in order with no loop. Stage 4, release, in the dev-team pack, has G3 where a review panel decides and G3.1 where you decide. Stage 5, run it, in the sre-oncall pack, uses its skills in order with no loop. Below them, the loops outside the lifecycle, from ship-a-draft at G5 to clarify at G14, and the packs that help at any stage.](../../docs/loops/operating-model.svg#gh-light-mode-only)](../../docs/loops/operating-model.svg)
[![Five stages on a rail, top to bottom. Stage 1, find the problem, in the product-manager pack, uses its skills in order with no loop. Stage 2, decide how to build it, in the solution-architect pack, uses its skills in order with no loop. Stage 3, build, in the dev-team pack, uses its skills in order with no loop. Stage 4, release, in the dev-team pack, has G3 where a review panel decides and G3.1 where you decide. Stage 5, run it, in the sre-oncall pack, uses its skills in order with no loop. Below them, the loops outside the lifecycle, from ship-a-draft at G5 to clarify at G14, and the packs that help at any stage.](../../docs/loops/operating-model-dark.svg#gh-dark-mode-only)](../../docs/loops/operating-model-dark.svg)

[Open the picture full size](../../docs/loops/operating-model.svg). It is generated from each loop's `loop.json`, so it changes when a loop does.

## The five stages

Start at the stage your work is in. A bug fix starts at build.

| Stage | Loop | Pack | It ends when |
|---|---|---|---|
| Find the problem worth solving | none: `feedback-synthesis` or `requirements-interview`, then `prd-draft` | `product-manager` | You agree the requirement |
| Decide how to build it | none: `context-graph` and `nfr-spec`, then `design-doc` and `architecture-diagrams`, then `threat-model`, `council-review` and `adr-generator` | `solution-architect` | A review panel accepts the design and you record the decision |
| Build it | none: `user-story-splitter` or `bug-triage`, then `feature-implement-loop`, then `pre-merge-review` | `dev-team` | The checks pass and you merge |
| Ship it | `release` | `dev-team` | Readiness is shown on evidence (G3) and you say go (G3.1) |
| Run it | none: `observability-plan`, `runbook-generator`, `incident-comms`, `postmortem-generator` | `sre-oncall` | You close the incident with a postmortem |

Some packs help at any stage: `stakeholder-comms` to explain the work, `design` for on-brand decks, `research` to answer a question with sources, `converters` to move between formats, `trackers` to keep Jira, Linear or GitHub Projects straight, and `data-analytics`, `grc`, `infra-as-code`, `experience-design`, `ai-engineering`, `api-builder` and `skill-engineering` for their specialist work.

## Find the problem worth solving

You turn a request, a complaint or a strategy question into a requirement someone has agreed to. Run `feedback-synthesis` on raw signal, or `requirements-interview` or `user-journey-map` when you have people to ask, then `prd-draft`. No check can tell you that you solved the wrong problem well, so you agree the requirement before design starts. This stage had a loop with a ratification gate; it was retired because its own skills did better without it. See [the product manager workflow](../tutorial/product-manager-workflow.md).

## Decide how to build it

You turn the requirement into a recorded decision. Run `context-graph` to read the decisions already in force and `nfr-spec` to set the quality targets, then `design-doc` and `architecture-diagrams`, and `threat-model` on the result. Then `council-review` puts the design to a panel of independent reviewers, and `adr-generator` writes the agreed decision down, one record per decision. A design mistake costs months once it is in code, so disagreement is kept, not smoothed over. This stage had a loop; it was retired after five measurements because its own skills did better without it. See [the solution architect workflow](../tutorial/solution-architect-workflow.md).

## Build it

Run `user-story-splitter` on new work or `bug-triage` on a reported defect, with `codebase-tour` first in a repository nobody on the change knows. Then `feature-implement-loop` implements the slice with adversarial review, and `pre-merge-review` runs your lint, type checks and tests through its gate script. The script's exit code decides: the agent cannot argue its way past a failing test. You decide whether to merge. This stage had a loop; it was retired after four measurements because its own skills did better without it. See [the dev-team workflow](../tutorial/dev-team-workflow.md).

## Ship it

The `release` loop plans the rollout and the way back, judges readiness on evidence at G3, and drafts the release notes. Then you make the go/no-go call at G3.1. The two questions are separate: G3 asks whether the change can ship, and G3.1 asks whether it should ship now. See [release a change](../how-to/release-a-change.md), and [from idea to shipped feature](../tutorial/idea-to-shipped-feature.md) for one release end to end.

## Run it

Run `observability-plan` to decide what to watch, `runbook-generator` for the runbook, `incident-comms` during an incident and `postmortem-generator` after it. You close the incident, and the postmortem's changes go back into the runbook. The skills already hand off to each other, which is why the loop this stage had was retired. See [from complaint to closed incident](../tutorial/complaint-to-closed-incident.md).

## Where the agent waits for you

The harder a mistake is to undo, the more the agent waits:

| A mistake here | Examples | Who decides |
|---|---|---|
| Can be undone cheaply | A failing test, a lint error | A script, by its exit code (`pre-merge-review`) |
| Costs months or users to undo | A design, a launch that is not ready | A review panel, with dissent recorded (`council-review`, G3) |
| Can't be undone, or is a judgment call | The problem you commit to, a merge, a go-live, closing an incident | You (G3.1, and the requirement, the merge and the incident yourself) |

Every gate answers from one shared set of verdicts:

| Class | Verdicts | What happens next |
|---|---|---|
| Pass | `READY`, `PROCEED`, `SHIP IT`, `VERIFIED` | The work moves on |
| Conditional | `PROCEED WITH CONDITIONS`, `SHIP WITH CHANGES`, `VERIFIED WITH OPEN ITEMS` | The work moves on, and the named items go with it |
| Revise | `REVISE`, `NOT READY`, `MAJOR REWRITE` | Back to an earlier stage, at most three times |
| Redirect | `RECONSIDER`, `SPLIT`, `WRONG ARTIFACT` | The work is the wrong shape, so it leaves the loop |
| Blocked | `BLOCKED` | Something is missing, and the agent names it |

## How to read a gate code

A gate code tells you where the work stopped. The whole number is the loop's place in the lifecycle: G3 is release. G0, G1, G2 and G4 belonged to the loops of the find, design, build and run stages, since retired. A decimal is a second gate inside the same loop, so G3.1 is the go/no-go that follows the G3 readiness review.

## Outside the lifecycle

The other loops are not stages. `ship-a-draft` wraps any document, at any stage: it collects the input properly, lets any skill draft, and has `doc-critique` check the result at G5. Each of the rest does one job beside the lifecycle: `research` (G7) a why question, `comply` (G8) a risky change, `measure` (G9) a dashboard's numbers, `modernize` (G10) a legacy rewrite, `ship-agent` (G12) an AI agent, `provision` (G13) a Terraform change and `clarify` (G14) a service people struggle with. Each stops for a person wherever only a person can decide.

## Install the loops you use

Each loop installs with the skills its stages run:

```bash
npx skilldrop-cli install --loop release
```

That installs the lifecycle's one loop, with its skills; install `product-manager`, `solution-architect`, `dev-team` and `sre-oncall` for the stages that use their skills in order. Name only the ones your team uses, or install every loop a pack holds with `npx skilldrop-cli install --loop --pack dev-team`. Then ask your agent to run one, for example: "Run the release loop on this change." See [the loops, stage by stage](../reference/loops.md) for every stage and skill, and [why loops](loops.md) for why they are built this way.
