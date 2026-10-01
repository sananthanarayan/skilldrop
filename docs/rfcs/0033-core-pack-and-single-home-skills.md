---
rfc: 0033
title: Core pack and single-home skills
status: implemented
date: 2026-10-01
author: sanjay-ananth
---

# RFC-0033: Core pack and single-home skills

## Problem / use case

RFC-0001 let a skill belong to several packs, so each role could install its full toolkit in
one command. That cost little while packs were only lists. It is now the main obstacle to the
physical `packs/<name>/` layout the maintainer plans (RFC-0032, **Forward compatibility**): a
folder can only sit in one place. 12 of 63 skills are in more than one pack, and so are 4 of
6 loops. Most of them are cross-role tools, not role tools: `brief-intake`, `doc-critique`,
`output-hygiene` and `council-review` appear wherever the `ship-a-draft` wrapper or a review
gate does.

Deciding where each skill lives is the hard part of that migration. Doing it now in
`packs.json` lets it be checked and adjusted before any folder moves.

## Fit check

Structural change: it amends RFC-0001's overlap rule and the `packs.json` contract.

- **Rule 2 (`skills/` stays flat)** is untouched. This RFC changes membership, not paths.
- **One-command install** is preserved. A pack can declare `requires: ["core"]`, and every
  installer (the CLI, `pack.py`, and the per-pack Claude plugins) installs the required pack
  with it. `--pack dev-team` still delivers the critique and review skills it did before.
- **Zero dependencies** is preserved: a stdlib check in `validate.py`, plain JS in the CLI.

## Proposal

**A `core` pack** for skills every role uses: `brief-intake`, `doc-critique`,
`output-hygiene` and `council-review`, plus the `ship-a-draft` wrapper loop. Every role pack
except `claude-api` (a specialist add-on with no overlap) declares `"requires": ["core"]`.

**Each other overlapping skill gets one home**, chosen by who produces its artifact. The tie-breaker
is a new rule: a pack contains every skill its loops run, counting the skills of the packs it requires.

| Skill | Was in | Now in | Why |
|---|---|---|---|
| `user-story-splitter` | product-manager, dev-team | dev-team | The `build` loop's `shape` stage runs it |
| `launch-readiness` | dev-team, sre-oncall | dev-team | Lives with the `release` loop and its other stages |
| `agents-md-generator` | solution-architect, dev-team | dev-team | Its artifact sits in the repo the team works in |
| `capacity-cost-model` | solution-architect, sre-oncall | sre-oncall | Capacity planning belongs to the team that runs the service |
| `data-contract` | solution-architect, ai-engineering | solution-architect | Alongside `api-contract-draft` and `db-schema-design` |
| `agent-threat-model` | solution-architect, ai-engineering | ai-engineering | Agent-specific; `threat-model` stays in solution-architect |
| `ai-use-case-triage` | product-manager, ai-engineering | ai-engineering | Alongside the other AI-adoption skills |
| `exec-summary` | product-manager, stakeholder-comms | stakeholder-comms | Written for non-technical decision-makers |

**Loops get one home too:** `ship-a-draft` → core, `discover` → product-manager, `design` →
solution-architect, `build` and `release` → dev-team, `operate` → sre-oncall.
`ai-engineering` and `stakeholder-comms` keep no loop of their own.

**Contract and checks.** `contracts/pack.schema.json` gains an optional `requires`. `validate.py`
fails when a skill or loop is in more than one pack, when `requires` names a missing pack or
the pack itself, or when a required pack requires another (one level only). It also fails
when a pack's loop runs a skill missing from both that pack and its required packs.
`profiles.json`'s `full` profile is fixed to list all 8 packs and 6 loops; it had been
missing `claude-api` and `release`.

**Installers.** `skilldrop install --pack X`, `install --loop --pack X`, `pack.py X --install`
and the per-pack plugins on the `plugins` branch all include `requires`. The CLI prints
`(includes core)`.

**Files touched:** `packs.json`, `profiles.json`, `contracts/pack.schema.json`, `validate.py`,
`bin/skilldrop.js`, `pack.py`, `build_marketplace.py`, `build_site.py`, README, AGENTS.md,
`assets/og.{svg,png}`, `llms.txt`, CHANGELOG, and `package.json`.

## Alternatives considered

- **Keep overlap and resolve it at migration time.** Rejected: the migration would then
  include unreviewed membership decisions, made while files are moving.
- **Profiles instead of `requires`** (agent-ready-repo's ADR-0025). Rejected for now. A
  profile is a separate install command, so `--pack dev-team` would quietly install less than
  it does today. `requires` keeps one command per role, and profiles stay as larger bundles.
- **No `core`, assign every shared skill to one role.** Rejected: `doc-critique` would then
  belong to one role while three others need it, and three of those four packs would lose it.

## Decision

Accepted 2026-10-01 together with RFC-0032's revised delivery order. It supersedes RFC-0001's
"a skill may belong to several packs". Implemented in [#27](https://github.com/sananthanarayan/skilldrop/pull/27).
