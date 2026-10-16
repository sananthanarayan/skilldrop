---
title: Install skills, packs and loops
summary: Install a role's pack, one skill, a loop or the reviewer subagents with the skilldrop CLI or the Claude Code plugin marketplace.
kind: how-to
---

# Install skills, packs and loops

Install the skilldrop pack for your role, a single skill, a loop or the reviewer subagents with one command, in Claude Code or any other agent.

Every command, flag and plugin detail is on [Install options](../reference/install-options.md).

## Find the pack for your role

A pack is the set of skills one role uses, and each role pack brings `core` with it. List them:

```bash
npx skilldrop-cli packs
```

You get every pack and its skills; `npx skilldrop-cli info --pack <name>` says what to try first.

## Install a pack with the CLI

The `skilldrop-cli` npm package copies a pack's skills into Claude Code's user folder:

```bash
npx skilldrop-cli install --pack product-manager
```

The skills land in `~/.claude/skills/` and load in every project. Add `--project` for the repo's `.claude/skills/`, or `--ide` for another tool, as [Install a skill into your IDE](install-per-ide.md) shows.

## Add the plugin marketplace in Claude Code

In Claude Code you can skip npm and add skilldrop as a plugin marketplace, once:

```text
/plugin marketplace add sananthanarayan/skilldrop
```

Claude Code then offers one plugin for the whole catalogue and one for each pack.

## Install a pack plugin

Install the plugin for your role's pack:

```text
/plugin install dev-team@skilldrop
```

The pack's skills, `core` included, invoke as `/dev-team:<skill-name>`; `skilldrop@skilldrop` takes the whole catalogue instead.

## Install one skill

Name the skill instead of a pack:

```bash
npx skilldrop-cli install prfaq
```

Add `--with-related` to also take the skills it hands work to; `npx skilldrop-cli list` names every skill.

## Install a loop

A loop runs skills in stages with a gate between each, and installing one brings the skills its stages use:

```bash
npx skilldrop-cli install --loop build
```

The loop installs as a skill you invoke; `npx skilldrop-cli loops` lists every loop with its stages and gates.

## Add the reviewer subagents

A reviewer subagent reviews in its own context with its own tool allowlist, and the review panel installs them with the `pre-merge-review` skill that runs them:

```bash
npx skilldrop-cli install --panel review
```

Delegate by name afterwards: *"use the devils-advocate agent on this diff."* To keep what you installed current, see [Upgrade installed skills](upgrade-skills.md).
