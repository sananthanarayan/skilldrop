---
title: Skills that ship scripts
summary: The two skills with executable helpers — what they need on PATH, what environment variables they read, and how to invoke them from Claude Code or any other IDE.
kind: reference
---

# Skills that ship scripts

### Skill Usage

All skills are invoked in chat. Arguments are passed as plain text after the skill's trigger phrase (or via `$ARGUMENTS` when invoked as a slash command in Claude Code).

#### `architecture-diagrams`

Natural-language trigger (works in any IDE that has the skill installed):

> Draw me a Mermaid diagram of a three-tier web app on AWS with an ALB, two ECS services, and an RDS Postgres backend.

Slash-command form (Claude Code):

```
/architecture-diagrams three-tier web app on AWS with ALB, two ECS services, RDS Postgres
```

Everything after the slash command becomes `$ARGUMENTS` inside the skill.

#### `figma-diagrams`

Natural-language trigger:

> Inspect the structure of this Figma file: https://figma.com/file/abc123/MyArchitecture

Slash-command form (Claude Code):

```
/figma-diagrams inspect https://figma.com/file/abc123/MyArchitecture
/figma-diagrams post-comment https://figma.com/file/abc123/MyArchitecture "Looks good — ship it."
```

The skill parses `$ARGUMENTS` to figure out which Figma URL you mean and which action to take.
