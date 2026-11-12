---
rfc: 0087
title: Install into every tool the repo uses (--ide all)
status: implemented
date: 2026-11-12
author: sanjay-ananth
---

# RFC-0087: Install into every tool the repo uses (`--ide all`)

## Problem / use case

A team that works in Claude Code, Cursor and Codex has to run one install per tool, and keep the
copies in step with one `update` per tool. Forgetting one leaves a teammate on an old skill, or
on none. The CLI design doc listed IDE detection and `--ide all` as design-only, and
`docs/designs/future-ideas.md` carried it under Distribution.

## Fit check

A new `--ide` value. It reuses every existing target: each detected tool is installed exactly
as `--ide <tool> --project` installs it, wiring files included (Cursor's `.mdc` rule). Nothing
that works today changes, and no dependency is added.

## Proposal

**`--ide all` runs the command once per tool found in the current folder, at project scope.** A
tool is found by the files it keeps in a repo:

| Tool | Found by |
|---|---|
| Claude Code | `.claude/` or `CLAUDE.md` |
| Cursor | `.cursor/` or `.cursorrules` |
| Kiro | `.kiro/` |
| Codex | `.codex/` or `.agents/` |
| Antigravity | `.agents/` |
| GitHub Copilot | `.github/skills/`, `.github/copilot-instructions.md`, `.github/instructions/` or `.github/agents/` |

- **A bare `.github/` doesn't count.** Nearly every repo has one for CI, and counting it would put
  Copilot skills in every repo.
- **`AGENTS.md` alone doesn't count either,** because many tools read it.
- **A folder two tools share is one target.** Codex and Antigravity both read `.agents/skills/`,
  so it is installed once and the output names both.
- **Scope:** it works with `install`, `update`, `outdated`, `uninstall`, `diff` and `doctor`, and
  with `--local` and `--dry-run`. Agents, panels and profiles go to one tool at a time, because
  their files differ per tool. `--dest` and `--json` are refused with it, since the first picks
  the target another way and the second would print one report per tool. Commands that don't
  take a target ignore it.
- **When nothing is found, it stops** and lists what it looked for.
- **`doctor` lists the tools it finds** and where `--ide all` would install, in its text and its
  `--json` (`tools_here`).

## Alternatives considered

- **Detect by default, with no flag.** It would change where a plain `skilldrop install` goes,
  which today is always `~/.claude/skills`. An explicit flag changes nothing for anyone who
  doesn't use it.
- **`skilldrop install <skill>@<version>`**, the other Distribution idea, was dropped rather than
  built:
  - **Exact installs already exist.** A commit pin (`--from <git-url>#<sha>`) installs exact
    files, and the ledger records the commit.
  - **It needs history the npm package lacks.** The bundled catalogue holds only the current
    version of each skill, so resolving a version would mean cloning the repo, which adds
    network and git to a path that is offline today.
  - **It would reopen retired loops,** such as `install --loop build@0.4.0`.

  It is removed from the future ideas.

## Decision

Implemented in 1.18.0. `cli_smoke.js` checks the behaviour on every OS in CI:
- it installs into `.claude/`, `.cursor/` and `.agents/`;
- it skips a CI-only `.github/`;
- it installs the shared folder once;
- `doctor` lists the tools, and uninstall removes every copy;
- it refuses an empty folder and `--dest`.
