---
title: Versioning and what stays stable
summary: What skilldrop promises from 1.0.0 — the CLI, skill folders and names, scripts' flags and exit codes, loops, packs, the GitHub Action and plugin names — what each kind of release can change, and how deprecation and retirement work.
kind: reference
---

# Versioning and what stays stable

From 1.0.0, skilldrop follows [Semantic Versioning](https://semver.org) for the surfaces below. A
change that would break one of them waits for the next major version. The decision is
[RFC-0064](../../docs/rfcs/0064-one-point-oh-stability.md).

## What stays stable within 1.x

| Surface | Stable |
|---|---|
| The CLI, `skilldrop-cli` | Its commands and their flags, exit codes, and `--json` fields. The [install targets](install-targets.md). The `.skilldrop.json` ledger: any 1.x reads it ([updates and the ledger](update-and-ledger.md)). The `SKILLDROP_POLICY`, `SKILLDROP_AUDIT_LOG`, `SKILLDROP_LOOP_LOG` and `SKILLDROP_NO_STAR` variables |
| A skill's folder | The anatomy in the [skill contract](skill-contract.md): `SKILL.md`'s `name` and `description`, `manifest.json`'s fields, and what its `permissions` mean |
| A skill's name | An installed skill stays installable and updatable under its name |
| A skill's scripts | The flags and exit codes its `SKILL.md` documents, because loops and CI gate on them |
| Loops, packs and profiles | The [loop contract](loop-contract.md), `pack.json`, `profiles.json`, and each gate's verdict words |
| The GitHub Action | Its inputs and outputs ([reference](ci-action.md)) |
| Plugins | The plugin names, `<pack>@skilldrop` |

## What any release can change

- **A skill's instructions and its output.** Skills get better as they're measured, and that's
  the point.
- **New skills, loops, packs, commands, flags, fields and optional inputs.**
- **Messages, help text and report wording.** Also fixes that turn a crash into a clear error.
- **The site, the docs' wording, the evals and the benchmark numbers.**
- **The repository's own tooling:** `validate.py`, the site builders and `run_bench.py`.

## Version numbers

| Release | Example | Contains |
|---|---|---|
| Patch | 1.0.0 → 1.0.1 | Fixes. Improvements to a skill that keep its documented flags and exit codes |
| Minor | 1.0.1 → 1.1.0 | Anything added. Any deprecation. A skill's retirement |
| Major | 1.x → 2.0.0 | A break in a stable surface, after a deprecation in a minor release |

**Each skill has its own version** in its `manifest.json`, under the same rules. `skilldrop
outdated` compares them.

## Deprecation and retirement

- **A deprecated flag, command, field or input keeps working until the next major release.** The
  release that deprecates it says so in the [changelog](../../CHANGELOG.md), and the CLI warns
  when it's used.
- **A skill that stops beating the plain agent is retired** ([how skills are
  checked](https://sananthanarayan.github.io/skilldrop/evals/)). It keeps a record naming what to
  use instead, for at least one minor release. `skilldrop outdated` and `skilldrop update` tell
  anyone who has it installed. The installed copy keeps working.

## Supported runtimes

- **Node.js 16.7 or later for the CLI,** as declared in the package. CI runs the CLI's smoke test
  on each runner's current Node, on Linux, macOS and Windows.
- **Python 3.9 or later for the skills' scripts.** Python 3.9 is past its end of life, but it's
  the `python3` that macOS ships, so the scripts keep supporting it. CI runs the unit tests on
  3.9 on Linux, and on each runner's current Python on Linux, macOS and Windows.

Raising either floor is a minor release with a changelog entry.
