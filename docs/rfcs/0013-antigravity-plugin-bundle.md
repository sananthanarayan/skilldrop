---
rfc: 0013
title: Antigravity agent target
status: implemented
date: 2026-07-26
author: sananthanarayan
---

# RFC-0013: Antigravity agent target

> **Rewritten 2026-07-26.** The first draft of this RFC designed a plugin-bundle emitter, on the premise that "Antigravity has no per-user agents directory — subagents exist only inside a plugin bundle." **That premise was false.** The original text is superseded rather than kept, because it documented a design for a problem that does not exist, and leaving it would send an implementer down a bundle build for no reason. What was wrong and why is recorded below.

## Problem / use case

Antigravity was the last target refusing `--agent`. Three times running, a target was filed as blocked and turned out to be blocked on a fact nobody had looked up:

| Target | Claimed blocker | Actual blocker |
|---|---|---|
| Kiro | tool vocabulary "never confirmed" | documented at kiro.dev all along |
| Codex | `.toml` schema "never confirmed" | documented in OpenAI's own docs |
| Antigravity | "no agents directory — plugin bundles only" | **there are two agent directories** |

[Antigravity's subagents documentation](https://antigravity.google/docs/subagents) states the discovery locations plainly:

| Scope | Path |
|---|---|
| Workspace | `.agents/agents/<name>.md` |
| Global | `~/.gemini/config/agents/<name>.md` |
| Plugin bundle | `plugins/<plugin>/agents/` |

The plugin bundle is the *third* option. The survey (`ide-primitive-coverage.md`, iteration 4) found the plugin layout first and generalised from it without checking whether a simpler path existed — the same error, in the same place, three times.

## Fit check

Structural change to the CLI, same shape as the Kiro and Codex emitters shipped in [RFC-0012](0012-subagent-installation.md): a frontmatter projection over a byte-identical body. No skill folder moves, nothing is executed, and the agent's system prompt passes through unchanged.

## What the format requires

Markdown with YAML frontmatter — the shape the agent files already are:

```markdown
---
name: code-auditor
description: Specialized subagent for security audits…
tools: [view_file, grep_search, run_command]
subagent: true
model: pro
---
…body becomes the system prompt…
```

- **`subagent: true` is required.** Without it the agent exists but `invoke_subagent` cannot reach it — a silent failure, which is why it is emitted unconditionally.
- `model` accepts `inherit | flash | pro`. Both shipped agents already declare `model: inherit`, which is valid as-is.
- Tool names are a third distinct vocabulary.

## Tool mapping

Confirmed from the example in Antigravity's own subagents doc:

| skilldrop / Claude Code | Antigravity |
|---|---|
| `Read` | `view_file` |
| `Grep` | `grep_search` |
| `Bash` | `run_command` |
| `Glob` | **no equivalent** |

Antigravity's file tooling is `view_file` / `list_dir` / `grep_search` / `write_to_file`; no glob-style pattern search appears in any primary source. `Glob` is therefore **named and dropped**, not mapped to `list_dir` — those are different operations, and quietly substituting one for the other is precisely the mistranslation this convention exists to prevent.

Only primary-confirmed mappings are included. Anything else warns, exactly as the Kiro emitter does.

## Proposal

- `--ide antigravity` for `--agent`: default `~/.gemini/config/agents/<name>.md`, `--project` → `.agents/agents/<name>.md`. Mirrors `--ide claude`'s user/project split.
- Frontmatter rewritten to `name`, `description`, `tools` (mapped), `subagent: true`, and `model` when it is one of Antigravity's accepted values. Body copied through untouched.
- Unmapped tools named in the output.

## The plugin bundle, retained as a future idea

The bundle is no longer the price of entry, but the idea that made it interesting survives: it is the only format where **skills, agents, and hooks ship as one registerable unit**, which is what a skilldrop pack already means. `plugin.json` needs only a `name`; the layout is `plugin.json` + `skills/` + `agents/` + `rules/` + `hooks.json`.

If it is ever built, one constraint from the first draft still holds: **emit the bundle and print `agy plugin install <path>`, never run it.** The bundle contains system prompts, and skilldrop has never executed anything on a catalog's behalf.

Deferred with no scheduled trigger. Direct agent installation now covers the actual use case.

## Alternatives considered

- **Emit a plugin bundle (the original proposal):** rejected — solves a problem that does not exist, and asks the user to register a plugin to get two markdown files.
- **Map `Glob` to `list_dir`:** rejected — different operations. A dropped tool is visible; a wrong one is not.
- **Write to `.agents/agents/` by default instead of the global path:** rejected for consistency — every other target defaults to user scope with `--project` for the repo.

## Decision

Implemented as proposed. Antigravity is no longer refused; every surveyed target now installs.
