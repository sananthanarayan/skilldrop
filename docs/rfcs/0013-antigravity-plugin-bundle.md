---
rfc: 0013
title: Antigravity plugin bundle
status: draft
date: 2026-07-26
author: sananthanarayan
---

# RFC-0013: Antigravity plugin bundle

## Problem / use case

Antigravity CLI is the last target that refuses `--agent`, and it refuses for a different reason than Codex did. Codex was a **fact gap** — an unconfirmed schema, closed by reading the docs. Antigravity is a **shape mismatch**: it has no per-user agents directory. Subagent templates exist only inside a plugin bundle at `~/.gemini/antigravity-cli/plugins/<plugin>/agents/`. There is nothing to look up; the question is whether skilldrop should emit a bundle it owns.

Antigravity does read `.agents/skills/` for project skills, so **skills already work** via `--dest .agents/skills`. Only agents and hooks are unreachable.

## Fit check

Structural change to the CLI. It does not touch skills, `packs.json`, or any skill folder. The premise it tests is different from previous target work: every target so far wrote **one file per primitive** into a directory the tool already watches. A plugin is a **container** — a manifest plus subdirectories — that the user must register with a command.

That collides with a standing constraint worth restating: **install copies files and never executes catalog content.** So this RFC can emit a bundle; it must not run `agy plugin install`. The user runs that themselves, on a directory they can read first.

## What the format actually requires

Confirmed at [antigravity.google/docs/cli/plugins](https://antigravity.google/docs/cli/plugins):

```json
{
  "$schema": "https://antigravity.google/schemas/v1/plugin.json",
  "name": "skilldrop",
  "description": "Portable skills and reviewer subagents."
}
```

- **`name` is the only required field** — `^[a-zA-Z0-9-_]+$`. `description` and `$schema` are optional. `additionalProperties: false`, so nothing else may be added.
- Bundle layout: `plugin.json` (required) plus optional `skills/`, `agents/`, `rules/`, `mcp_config.json`, `hooks.json`.
- Registration: `agy plugin install /path/to/local/plugin`, with `list` / `enable` / `disable` / `uninstall` alongside.

The manifest is trivial. The design questions are all about what goes *in* the bundle.

## The interesting part

This is the **first target where skills, agents, and hooks ship as one unit** — which is exactly what a skilldrop pack already means conceptually. Everywhere else a pack is a named list that expands into N independent copies. Here it could be a single artifact: `skilldrop install --pack sre-oncall --ide antigravity` emitting one bundle containing that pack's skills, any agents they delegate to, and any hooks they declare.

That is either the most natural expression of packs yet, or scope creep wearing a nice hat. This RFC exists to decide which.

## Decisions this RFC must settle

### 1. One bundle per pack, or one bundle named `skilldrop`?

- **(a) One bundle per pack — recommended.** `skilldrop-sre-oncall`, `skilldrop-dev-team`. Maps to how packs are already installed, lets a user enable/disable a role's toolkit as a unit with `agy plugin disable`, and keeps bundles small. Cost: a user wanting two packs registers two plugins.
- **(b) One `skilldrop` bundle, merged on each install.** Fewer registrations. Cost: every install rewrites a shared bundle, so uninstall has to diff rather than delete, and two packs' hooks land in one `hooks.json` with no owner.

### 2. Does the bundle carry hooks?

Antigravity's `hooks.json` is a real target for the RFC-0006 vocabulary, and putting it in the bundle is nearly free once the bundle exists. But hooks are opt-in everywhere else (`--with-hooks`), and a bundle that silently contains them would break that.

- **Recommended:** include `hooks.json` **only** under `--with-hooks`, matching every other target. A bundle without the flag carries `skills/` and `agents/` only.

### 3. Where is the bundle written?

- **(a) A local directory, then print the `agy plugin install` command — recommended.** Respects copy-never-execute, and the user can read the bundle before registering it. Default `./.skilldrop-antigravity/<name>/`, overridable with `--dest`.
- **(b) Straight into `~/.gemini/antigravity-cli/plugins/<name>/`.** One less step, but it writes into a staging directory the tool manages, may bypass whatever registration `agy plugin install` performs, and gives the user no moment to review a bundle that includes system prompts.

## Proposal (assuming the recommendations)

`skilldrop install --pack <name> --ide antigravity` writes:

```
.skilldrop-antigravity/skilldrop-<pack>/
├── plugin.json          # name + description, nothing else — additionalProperties is false
├── skills/<skill>/…     # byte-identical folders
└── agents/<agent>.md    # byte-identical; Antigravity reads markdown here
```

then prints `agy plugin install ./.skilldrop-antigravity/skilldrop-<pack>` for the user to run. `--agent <name> --ide antigravity` emits a bundle containing just those agents.

Uninstall removes the emitted directory and tells the user to run `agy plugin uninstall <name>` — skilldrop cannot unregister what it did not register.

## Alternatives considered

- **Do nothing; leave Antigravity refusing:** the honest baseline. Skills already work via `--dest .agents/skills`, so this buys agents and hooks only, for a tool whose adoption skilldrop has no data on. **This is a legitimate outcome of the review.**
- **Write into the plugins staging directory directly:** rejected — see decision 3b.
- **Run `agy plugin install` for the user:** rejected outright. It would be the first time skilldrop executed anything on behalf of a catalog, and the bundle contains system prompts.
- **Wait for RFC-0010:** rejected as a reason to block — this is a container emitter, not a path-set question, exactly as RFC-0012's targets turned out not to be.

## Open question

**Is anyone asking for this?** Antigravity shipped as Gemini CLI's forced successor in June 2026. skilldrop has no usage signal from it, and this RFC is the largest per-target effort yet for the least-evidenced demand. The same trigger that governed subagent installation applies: build it when a user asks, or when a second tool adopts a bundle shape and the emitter stops being single-use.

## Decision

{Pending review. The recommendation is to accept the design and **not implement it yet** — the shape is now known well enough that it can be built in a day when demand appears.}
