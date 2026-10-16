---
title: Install a skill into your IDE
summary: Put a skill where Claude Code, Cursor, Kiro, Codex, Antigravity, GitHub Copilot or another agent reads it, by copying the folder or with one CLI flag, then install its dependencies.
kind: how-to
---

# Install a skill into your IDE

Put a skilldrop skill where your coding agent reads it, by copying its folder from a clone of the repo or with one flag on the [CLI](install.md).

Every skill is a plain folder at `packs/<pack>/skills/<skill-name>/`, so this works for any pack; the examples use `architecture-diagrams` from the `solution-architect` pack. Paths, scopes and per-tool details are on [Install targets and dependencies](../reference/install-targets.md).

## Copy a skill into Claude Code

Copy the skill folder itself, not its pack folder, into your user skills folder:

```bash
mkdir -p ~/.claude/skills && cp -R packs/solution-architect/skills/architecture-diagrams ~/.claude/skills/
```

Every project now has the skill: invoke it with `/architecture-diagrams` or describe the task. Copy into `.claude/skills/` instead to share it with the repo.

## Install into Cursor

Cursor has no skills folder, so the CLI copies the skill and writes a project rule that points at it:

```bash
npx skilldrop-cli install architecture-diagrams --ide cursor
```

The skill lands in `.cursor/skills/` and the rule in `.cursor/rules/architecture-diagrams.mdc`, which fires when your request matches the skill's description.

## Copy a skill into Kiro

Kiro IDE and Kiro CLI read the same skills folder:

```bash
mkdir -p .kiro/skills && cp -R packs/solution-architect/skills/architecture-diagrams .kiro/skills/
```

Kiro matches the skill by its `name` and `description`; copy into `~/.kiro/skills/` to reach every project.

## Install into Codex, Antigravity or Copilot

Each tool has its own `--ide` value:

```bash
npx skilldrop-cli install --pack dev-team --ide codex
```

The pack lands in `~/.codex/skills/`; use `antigravity` or `copilot` for those tools, and add `--project` to install into the repo instead.

## Try skills in a repo you don't own

`--local` installs into the repo and hides every file it writes from git:

```bash
npx skilldrop-cli install --pack dev-team --local
```

`git status` stays clean, nothing can be committed by accident, and `uninstall --local` removes the files.

## Install into another agent

For Continue, Cline, Aider or another tool without a skills folder, copy the skill into the repo:

```bash
npx skilldrop-cli install architecture-diagrams --dest skills
```

Attach `skills/architecture-diagrams/SKILL.md` to your prompt (`@file` in Continue and Cline, `/add` in Aider) and tell the agent to follow it.

## Install a skill's dependencies

A skill that ships a `requirements.txt`, such as `figma-diagrams` or `deck-builder`, needs its Python packages; run this inside the copied folder:

```bash
python3 -m pip install -r requirements.txt
```

The packages listed under `deps` in the skill's `manifest.json` install; `figma-diagrams` also needs a Figma token in `FIGMA_TOKEN`.
