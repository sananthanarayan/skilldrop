---
rfc: 0064
title: 1.0.0 and what it promises
status: implemented
date: 2026-10-21
author: sanjay-ananth
---

# RFC-0064: 1.0.0 and what it promises

## Problem / use case

skilldrop has shipped 0.x releases since May 2026, under a rule that "1.0.0 waits for an
explicit stability commitment" (AGENTS.md, Releasing). A team deciding whether to adopt it reads
0.x as "this can break at any release", and they'd be right: nothing said what couldn't.

## Fit check

No skill or tooling changes. This sets what the version number means from 1.0.0 on.

## Proposal

**From 1.0.0, skilldrop follows Semantic Versioning for the surfaces below.** A change that
breaks one of them waits for 2.0.0.

| Surface | What stays stable within 1.x | What may change in any release |
|---|---|---|
| **The CLI** (`skilldrop-cli`) | commands and their flags; exit codes; the install targets in [install-targets](../../guides/reference/install-targets.md); the `.skilldrop.json` ledger, which any 1.x reads; `--json` output fields; the `SKILLDROP_*` environment variables | new commands, flags and fields; help text and messages |
| **A skill's folder** | the anatomy in [contracts/skill.schema.json](../../contracts/skill.schema.json): `SKILL.md` frontmatter `name` and `description`, `manifest.json`'s fields, and its permissions meaning | new optional manifest fields |
| **A skill's name** | an installed skill stays installable and updatable under its name | its instructions and output, which improve in any release. Retirement follows the policy below |
| **A skill's scripts** | the flags and exit codes its `SKILL.md` documents, because loops and CI gate on them | new flags; report wording; fixes that turn a crash into a clear error |
| **Loops, packs and profiles** | `loop.json` (RFC-0028), `pack.json`, `profiles.json`, and the gate verdict words in [contracts/terminals.json](../../contracts/terminals.json) | new loops, packs, profiles and stages |
| **The GitHub Action** (`action.yml`) | its inputs and outputs | new optional inputs |
| **The plugin marketplace** | plugin names (`<pack>@skilldrop`) | new plugins |

**Not covered:**
- the site;
- the docs' wording;
- the evals;
- benchmark numbers;
- the repo's own build and lint scripts (`validate.py`, `build_*.py`, `run_bench.py`).

**Version numbers from 1.0.0**
- **Patch (1.0.x):** fixes, and improvements to a skill's instructions or scripts that keep its
  documented flags and exit codes.
- **Minor (1.x.0):** anything added, such as a new skill, loop, pack, command, flag or field, and
  any deprecation.
- **Major:** a break in a covered surface.

This replaces the 0.x rule of bumping the third digit for everything.

**Deprecation and retirement**
- **A covered surface is deprecated in a minor release** with a CHANGELOG entry and, for the CLI,
  a warning when it's used. It keeps working until the next major.
- **A skill is retired when it stops beating the plain agent** (RFC-0046). It keeps a record in
  `catalogue.json` naming what to use instead. `skilldrop outdated` and `update` tell anyone who
  has it installed. The record stays for at least one minor release.
- **Retirement isn't a break.** The installed copy keeps working, and no surface's shape changes.

**Supported runtimes**
- **Node.js 16.7 or later for the CLI,** as declared in `engines` in `package.json`. CI runs the
  CLI smoke test on each runner's current Node, on Linux, macOS and Windows.
- **Python 3.9 or later for skill scripts.** CI runs the unit tests and `validate.py` on 3.9 (a
  new `python-floor` job), and on each runner's current Python on all three systems.

Raising either floor is a minor release with a CHANGELOG entry.

## Alternatives considered

- **Stay on 0.x.** It's honest about change, but it tells adopters nothing is stable, which is no
  longer true.
- **Promise skill output too.** A skill's answers get better as models and evidence change. That
  improvement is the point, so it can't be frozen.
- **CalVer.** Dates say when something shipped, not whether upgrading is safe, which is the
  question an adopter asks.

## Decision

Accepted. Released as 1.0.0.
