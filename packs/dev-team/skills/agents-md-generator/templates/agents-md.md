# AGENTS.md — {project name}

> {One line: what an agent needs to know it is working on.}

## Repo in one paragraph

{What this is, what it produces, and the one structural fact an agent must hold. 3–5 lines.}

## Commands

<!-- Every row traces to a file. No row may be inferred from ecosystem convention. -->

| Task | Command | Source |
|---|---|---|
| Install | `{cmd}` | `{file}` → `{key}` |
| Build | `{cmd}` | `{file}` → `{key}` |
| Test | `{cmd}` *or* `[missing: no test command in CI or manifests]` | `{file}` → `{key}` |
| Lint | `{cmd}` | `{file}` → `{key}` |
| Run locally | `{cmd}` | `{file}` → `{key}` |

{Drop the Source column from the final file if it crowds the budget — but only after every row has been verified with it present.}

## File placement

| Kind | Where |
|---|---|
| {thing} | `{path}` |

## Conventions

<!-- Each line must pass: without it, would a competent agent do the wrong thing? -->

- **{Rule stated as a rule.}** {One clause of why, only if the why changes how it is applied.}

## Do not

- {Path, command, or action that must never happen unattended — concrete.}
- {Generated artifacts that must not be hand-edited, and the command that regenerates them.}

## Pointers

- {Deeper doc}: `{path}`
- {Architecture / design}: `{path}`

<!--
Line budget: 150. Provenance for every command was verified at generation time.
Commands marked [missing] are findings, not omissions — the repo has no such command.
-->
