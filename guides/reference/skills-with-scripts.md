---
title: Skills that ship scripts
summary: Where a skill with scripts declares what they need, which two need packages beyond the standard library, and how to invoke a skill from Claude Code or any other IDE.
kind: reference
---

# Skills that ship scripts

Many skills ship helper scripts in a `scripts/` folder, and each one declares what its scripts need in its own `manifest.json`: `deps` for packages, `env` for environment variables, and `permissions` for the hosts, commands and files the scripts touch. You can read that block before you install.

Most scripts run on the Python standard library. Two need a package: `deck-builder` (`python-pptx`) and `figma-diagrams` (`requests`). [Installing dependencies](../how-to/install-per-ide.md#installing-dependencies) covers both.

## Invoke a skill

All skills are invoked in chat. Arguments are passed as plain text after the skill's trigger phrase (or via `$ARGUMENTS` when invoked as a slash command in Claude Code).

### `architecture-diagrams`

Natural-language trigger (works in any IDE that has the skill installed):

> Draw me a Mermaid diagram of a three-tier web app on AWS with an ALB, two ECS services, and an RDS Postgres backend.

Slash-command form (Claude Code):

```
/architecture-diagrams three-tier web app on AWS with ALB, two ECS services, RDS Postgres
```

Everything after the slash command becomes `$ARGUMENTS` inside the skill.

### `figma-diagrams`

Natural-language trigger:

> Inspect the structure of this Figma file: https://figma.com/file/abc123/MyArchitecture

Slash-command form (Claude Code):

```
/figma-diagrams inspect https://figma.com/file/abc123/MyArchitecture
/figma-diagrams post-comment https://figma.com/file/abc123/MyArchitecture "Looks good — ship it."
```

The skill parses `$ARGUMENTS` to figure out which Figma URL you mean and which action to take.
