---
rfc: 0012
title: Subagent installation (plain-copy targets only)
status: implemented
date: 2026-07-26
author: sananthanarayan
---

# RFC-0012: Subagent installation (plain-copy targets only)

## Problem / use case

`agents/` is skilldrop's second primitive and the only one with no distribution. It is not in `package.json` `files`, so npm users never receive it, and the CLI has zero commands that touch it — no install, no list, no uninstall. The two agents can only be obtained by cloning the repo and copying by hand from a table in `agents/README.md`.

That gap is now load-bearing in two places:

- **`feature-implement-loop` degrades for everyone who installed via npm.** It says "delegate to the `devils-advocate` subagent" where one exists, otherwise sweep the four lenses inline. The fallback is by design and works — but the better path is unreachable for CLI users through no choice of their own.
- **The catalogue claims a primitive it does not deliver.** skilldrop describes itself as packs of skills, subagents, and hooks. Skills install in one line. Hooks wire under `--with-hooks`. Subagents don't install at all.

## Fit check

Structural change to the CLI. Touches golden rules 2 and 4 and breaks neither: `agents/` does not move, agent files are copied byte-identical exactly as skills are, and the new surface is documented here rather than invented at the call site.

**Scope is deliberately bounded to what does not depend on [RFC-0010](0010-install-target-table.md).** That RFC has three open decisions about the target model, and building a per-tool projection layer for agents now would commit to answers it hasn't given. So this RFC ships **only the targets that are a plain copy** — no transformation, no generated wrapper file, nothing that presumes a path-set design:

| Target | Mechanism | In scope? |
|---|---|---|
| Claude Code | `~/.claude/agents/<name>.md` or `.claude/agents/` — copy as-is; the frontmatter is already Claude Code's format | ✅ |
| Any directory | `--dest <dir>` — copy as-is | ✅ |
| GitHub Copilot | `.github/agents/<name>.agent.md` — needs a filename change | ❌ deferred: a rename is a projection |
| Kiro | `.kiro/agents/<name>.json` — needs a generated JSON wrapper around a `file://` prompt | ❌ deferred: generation is a projection |
| Codex | `.codex/*.toml` — schema unconfirmed by the survey | ❌ deferred: would be a guess |
| Antigravity | plugin-bundle `agents/` — copy into a bundle the user owns | ❌ deferred |

Deferring four targets is the point, not a shortfall. Claude Code is the one tool where the file already *is* the native format, so it needs no design decision at all.

## Proposal

- **`agents/` added to `package.json` `files`.** Justified now, because a command exists that uses it.
- **`skilldrop agents [--from <src>]`** — list the agents in a catalog: name, what it reviews, description.
- **`skilldrop install --agent <name…>`** — copy agent files to the agent target. Composes with `--project`, `--dest`, and `--from` exactly as skill installs do.
- **`skilldrop uninstall --agent <name…>`** — remove them and their ledger entries.
- **A structural gate mirroring the skill gate**: an agent is refused before copying if the file is missing, its frontmatter `name` disagrees with its filename, or it has no `description`. Same rules `validate.py` enforces in-repo, applied to third-party catalogs at install time.
- **Unsupported `--ide` targets print the reason and the manual route**, per RFC-0006's degradation contract — never a silent skip, never an invented path.
- **Agents are absent from `update` / `outdated`.** Agent frontmatter has no `version` field, so there is nothing to compare. They live in a different destination directory from skills, so their ledger is naturally separate and the two cannot interfere. Adding versions to agents is a future change, not a prerequisite.

Third-party catalogs (RFC-0003) get this free: any catalog with an `agents/` directory is installable, and the same review-before-use warning applies — more pointedly, since an agent is a system prompt.

## Alternatives considered

- **Wait for RFC-0010 and build all six targets at once:** rejected — Claude Code needs no projection design, so blocking a byte-copy on an unrelated decision is delay with nothing bought. The four deferred targets genuinely need RFC-0010; this one does not.
- **Ship `agents/` in npm `files` without a command:** rejected outright — the files would be present in a package directory with nothing to surface them, and `npx` leaves no persistent install to dig through. Motion without effect.
- **Fold agents into `skills/`:** rejected — a subagent's `tools` allowlist and separate context are a contract a skill cannot express, and merging would put a persona into the slash-command namespace where it does not belong.
- **A `--with-agents` flag on skill installs** (auto-install a skill's referenced subagents): deferred, and attractive — `feature-implement-loop` naming `devils-advocate` is exactly the link that would drive it. It needs a manifest field to declare the dependency; `related` is for skills. Worth its own RFC once agents have versions.
- **Do nothing:** rejected — this is the last primitive with no distribution path, and the claim that skilldrop installs subagents is not currently true.

## Decision

Accepted and implemented. `skilldrop agents`, `install --agent`, `uninstall --agent`, the structural gate, and `agents/` in npm `files` shipped together. A new CLI flag is a change to the public surface, so this releases as a **minor** bump (`0.4.x` → `0.5.0`) per the versioning rule in AGENTS.md.

## Follow-up (2026-07-26): Kiro and Copilot un-deferred

The deferral above named a reason, and the reason turned out to be wrong for two of the four targets.

**Kiro.** It was deferred because generating the JSON needed a tool-name vocabulary the survey never captured. That vocabulary is documented — [kiro.dev/docs/cli/reference/built-in-tools](https://kiro.dev/docs/cli/reference/built-in-tools/) enumerates all 19 built-ins — and the mapping for both shipped agents is exact, not inferred: `Read`→`read`, `Grep`→`grep`, `Glob`→`glob`, `Bash`→`shell`. The gap was in the survey, not in Kiro's docs. Now shipped as `--ide kiro`.

Two decisions inside the emitter worth recording:

- **The prompt is inlined, not a `file://` reference.** Kiro's example uses a relative `file://` path, but whether it resolves against the workspace root or the JSON file is not stated, and a wrong path fails *silently* — the agent loads with no instructions. A self-contained file cannot fail that way. The duplication is generated at install time from one source, exactly as Cursor's `.mdc` already works.
- **`allowedTools` is deliberately omitted.** It controls auto-approval, so leaving it out means the user is prompted per tool call — the right default for a reviewer agent, and it sidesteps [kirodotdev/Kiro#6714](https://github.com/kirodotdev/Kiro/issues/6714), where `allowedTools` does not load as configured in kiro-cli 1.28.1.
- **A tool with no Kiro equivalent is named and dropped, never guessed at.** Silently mistranslating a permission is the failure `agent-threat-model` exists to catch.

**Copilot.** Deferred as "a rename is a projection," which was true and also trivial: `<name>.agent.md`, no content change, no vocabulary question. Shipped as `--ide copilot`.

**Still refusing, with the reason printed:** Codex (`.codex/*.toml` schema unconfirmed — emitting one would be a guess) and Antigravity (a plugin bundle the user owns). Neither is blocked on RFC-0010 either; both are blocked on a fact nobody has confirmed.

Note the asymmetry this leaves: `--ide copilot` and `--ide kiro` work for `--agent` but `--ide copilot` is still unknown for skills. That inconsistency is real and is exactly what RFC-0010's target table exists to remove.

Released as **0.6.0** — `--agent` gained targets, which is a change to the public surface.
