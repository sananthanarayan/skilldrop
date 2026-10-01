---
rfc: 0031
title: Release loop
status: implemented
date: 2026-10-01
author: sanjay-ananth
---

# RFC-0031: Release loop

## Problem / use case

The loops cover discover → design → build → operate, but nothing covers the step between
**merged** and **live**. `build` ends at G2.1, where a human merges. `operate` begins at
`instrument`, which assumes the service is already running. The work in between is how to
roll out, how to undo it, whether you are ready, and who you tell. That work is where a
merged change most often becomes an incident, and no loop sequences it.

Two of the parts already exist and belong to no loop:

- [`migration-plan`](../../skills/migration-plan/SKILL.md) already produces "a phased
  migration or rollout plan". Every phase is reversible or names its point of no return, and
  observable gates sit between phases.
- [`release-notes`](../../skills/release-notes/SKILL.md) turns the git range into a
  customer-facing version and an internal version.

Both are in the `dev-team` pack, but neither appears in any `loop.json`. A team that runs
`build` and then `operate` skips them by construction.

## Fit check

This is a structural change (a new loop) plus one new skill. The golden rules it touches:

- **Rule 7 (a skill never invokes a skill; a loop orders them)** is respected. `release`
  orders `migration-plan`, `launch-readiness`, `release-notes` and `council-review`, and none
  of them calls another.
- **Rule 8 (`Quality bar` + `Anti-patterns`)** is met. `LOOP.md` and the new skill each ship both.
- **Verdict vocabulary** is unchanged. Every gate uses verdicts already in
  `contracts/terminals.json`, so no new word is added for an existing outcome.
- **`skills/`** is untouched apart from one added folder.

The new skill, **`launch-readiness`**, passes the four criteria:

- **Concrete artifact:** a go/no-go readiness report. It has one row per check (rollback
  path, an alert and runbook for each new failure mode, NFR targets measured rather than
  asserted, comms drafted, data and privacy sign-off), each with an owner and a status of
  `met` / `not met` / `n/a — because`.
- **Portable:** markdown only, with no scripts in v1, so a plain folder copy works in every IDE.
- **Opinionated:** a check with no evidence link counts as `not met`. A missing rollback path
  blocks the launch on its own, whatever else passes. `n/a` requires a reason.
- **Category:** engineering delivery, alongside `migration-plan` and `release-notes`.

## Proposal

Add `loops/release/` (`LOOP.md` + `loop.json`). It has `kind: loop` and `cap: 3`.

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `plan` | generate | `migration-plan` | — |
| 2 | `ready` | verify | `launch-readiness` | **G2.5** review: `PROCEED`, `PROCEED WITH CONDITIONS`, `REVISE`, `BLOCKED`. `revise_to: plan` |
| 3 | `announce` | generate | `release-notes` | — |
| 4 | `go` | gate | `council-review` | **G2.6** human: `PROCEED`, `PROCEED WITH CONDITIONS`, `REVISE`, `RECONSIDER`, `BLOCKED`. `revise_to: plan` |

- **Gate ids** follow G2 (build) and come before G3 (operate). The ids sit where the loop
  sits in the lifecycle and match `G<n>[.<n>]`.
- **`ready` comes before `announce`** so nobody announces a launch that then fails readiness.
- **`go` is human and separate from `ready`.** Readiness says whether the release *can* ship.
  The go decision says whether it *should* ship now (timing, freeze windows, who is on call).
  `RECONSIDER` covers "ready, but not this week".
- **Hand-offs to `operate`** sit on the `launch-readiness` manifest, since loops have no
  hand-off field. When the readiness report finds no alert for a new failure mode, it hands
  off to `observability-plan`. When it finds an alert with no runbook, it hands off to
  `runbook-generator`. Each hand-off has an inline fallback, as required.
- **Packs:** add `release` to `dev-team` and `sre-oncall` in `packs.json`, and add
  `launch-readiness` to both packs and to the `run-and-recover-the-service` outcome.
- **Model tier:** `standard` for `launch-readiness`. It checks each item against the evidence
  it has, which does not need adversarial reasoning. Because it is not heavy-tier, an
  `examples/` oracle is not required, but one ships anyway.

**Files touched:** `loops/release/{LOOP.md,loop.json}`,
`skills/launch-readiness/{SKILL.md,manifest.json,templates/readiness-report.md,evals/}`,
`packs.json`, `model-routing.json`, the regenerated `docs/loops/` and site, `CHANGELOG.md`,
`package.json` (third-digit bump), the GitHub About counts, and this RFC (marked `implemented`).

## Alternatives considered

- **Fold release into `build` as stages 5–7.** This was rejected. Loops are split by
  reversibility and decision authority (RFC-0028). A merge can be reverted with a commit, but
  a launch that has touched data or users often cannot. The go decision is also made by a
  different person from the merge, so they are different gates.
- **New `rollout-plan` and `rollback-plan` skills.** This was rejected for now.
  `migration-plan` already covers phased rollout and per-phase reversibility, and two
  near-duplicates would make the catalogue harder to read. Revisit if `plan` keeps being
  misused for pure feature-flag rollouts with no data change.
- **Put `dependency-upgrade-review` in this loop.** This was rejected. Reviewing a Dependabot
  or Renovate PR is a *merge* decision, so it belongs in `build` as an alternative to
  `pre-merge-review` at G2. It is out of scope here and gets its own RFC.
- **Do nothing.** This was rejected. The gap is structural, not cosmetic: `migration-plan` and
  `release-notes` stay unsequenced, and following the loops as written leads straight from
  merge to "instrument a running service".

## Decision

Accepted 2026-10-01. `release` ships as the fifth lifecycle loop with one new skill,
`launch-readiness`, in the same PR as this RFC
([#25](https://github.com/sananthanarayan/skilldrop/pull/25)).
