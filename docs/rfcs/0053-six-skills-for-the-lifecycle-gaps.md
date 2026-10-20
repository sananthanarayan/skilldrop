---
rfc: 0053
title: Six skills for the gaps between the loops
status: accepted
date: 2026-10-20
author: sanjay-ananth
---

# RFC-0053: Six skills for the gaps between the loops

## Problem / use case

The 2026 reviews named six jobs that people bring to an agent, that the catalogue has no
skill for, and where a capable agent working alone gets the important part wrong:

- **A dependency-upgrade pull request** gets merged on a green check. Nobody reads the
  releases it skipped, confirms that the pinned commit is the tagged one, or asks whether CI
  ran the code that changed. PR #24 was reviewed this way by hand.
- **A feature-flag rollout** gets thresholds nobody can test ("monitor errors"), and canary
  steps too short to detect the regression they are meant to catch. The plan says nothing
  about what turning the flag off doesn't undo. `migration-plan` covers data and schema
  changes, not exposure of a code path.
- **A pile of feedback** (tickets, NPS verbatims, interview notes) gets summarised by
  mentions instead of people. The loudest feature request becomes the theme, and quotes are
  paraphrased. This is a gap in the `discover` loop's `gather` stage.
- **An unfamiliar repository** gets a tour from its README. Commands are guessed, and the
  stale claims the code contradicts go unnoticed. This is a gap in the `build` loop's
  `shape` stage.
- **A refactor** gets planned as a rewrite. There are no characterisation tests, no target
  and no stop point. `tech-debt-register` records the debt; nothing plans paying it down.
- **Which MCP servers to connect** gets answered with a list of popular servers and broad
  scopes. Some of the names are invented, and write access lands on review stages.

## Fit check

- **Concrete artifact:** each skill produces one artifact:
  - a merge verdict with its checks;
  - a rollout plan with per-step thresholds and durations;
  - a theme table with counts by distinct person;
  - a cited tour doc;
  - a step-by-step refactor plan;
  - a per-stage pairing table.
- **Portable:** plain folders. The scripts are standard-library Python, read only the paths
  they are given, and contact no network.
- **Opinionated:** each one decides what a plain agent leaves open: the verdict rule, the
  duration from the arithmetic, the counting unit, the citation rule, the stop point, and
  read-only by default.
- **Category:** `dev-team` (four), `product-manager` (`feedback-synthesis`) and
  `ai-engineering` (`mcp-pairing`). `feedback-synthesis`, `codebase-tour` and `rollout-plan`
  join the `discover`, `build` and `release` loops as alternatives in an existing stage.

## Proposal

| Skill | Pack | Tier | Script | Bans |
|---|---|---|---|---|
| `dependency-upgrade-review` | dev-team | standard | the upgrade diff, old → new, by kind | merging on a green check alone; an unverified SHA pin |
| `rollout-plan` | dev-team | standard | per-step samples and hours to detect a regression | "monitor errors"; a step too short to see anything |
| `feedback-synthesis` | product-manager | standard | counts by distinct person and segment | counting mentions; a feature request as the theme |
| `codebase-tour` | dev-team | standard | the repo's manifests, CI commands, test dirs and generated files, read-only | README as fact; a guessed command |
| `refactor-plan` | dev-team | standard | — | the big-bang rewrite; refactoring untested code first |
| `mcp-pairing` | ai-engineering | standard | — | invented server names; write scope on a gate stage |

**Admission** follows RFC-0041 and RFC-0042: three evals by the author with fixtures, two
held-out evals by a writer who sees only the description, and a skill ships only if both
blind judges prefer it to plain Claude Code in at least half the held-out pairs over two
trials. A skill that fails is not shipped; RFC-0046 retired four that added only a format.

## Alternatives considered

- **Extend `migration-plan` with rollouts.** It is already long, and a flag rollout is a
  different job: exposure of a code path, not phases of a data move. It hands off instead.
- **Extend `source-synthesis` with feedback.** Sources answer a research question; feedback
  answers "what are people telling us", where the counting unit and the sampling biases
  differ. The two hand off to each other.
- **Leave MCP to the guide.** The guide is general; the failure is in tailoring it to a
  team's stages, where the plain agent widens scopes.

## Decision

Accepted. Four skills are admitted and ship in 0.16.30; two failed and are being revised.

Held-out evals, two per skill written by a writer who saw only the description, two trials,
two judges (`claude-sonnet-5-5`, `claude-opus-5-5`), on `claude-sonnet-5`:

| Skill | Pairs won, judge 1 | Judge 2 | Assertions met, skill | Without | $ per run, skill | Without |
|---|---|---|---|---|---|---|
| `codebase-tour` | 3 of 4 | 3 of 4 | 72% | 31% | 0.22 | 0.18 |
| `feedback-synthesis` | 3 of 4 | 2 of 4 | 72% | 47% | 0.50 | 0.15 |
| `mcp-pairing` | 2 of 4 | 4 of 4 | 94% | 38% | 0.18 | 0.12 |
| `dependency-upgrade-review` | 2 of 4 | 2 of 4 | 59% | 44% | 0.19 | 0.12 |
| `rollout-plan` | 0 of 4 | 2 of 4 | 72% | 38% | 0.27 | 0.10 |
| `refactor-plan` | 1 of 4 | 3 of 4 | 66% | 66% | 0.37 | 0.13 |

The first four clear the bar of half with both judges. `dependency-upgrade-review` clears it
exactly, so its next revision needs evals of its own.

**Not admitted:**
- **`rollout-plan`** met more of the checks, but judge 1 preferred plain Claude Code in every
  pair. Its replies led with sample sizes nobody had asked for, and gave dates and durations
  the input didn't support. The plain agent gave a practical, dated ramp built on the
  constraint that mattered.
- **`refactor-plan`** met no more checks than the plain agent. It wrote long documents
  nobody had asked for, and once put off its characterisation tests until an open PR merged.

Both are being revised and will be measured on fresh held-out evals before they ship.
