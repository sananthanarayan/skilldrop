# Core

The cross-role toolkit every pack builds on: structured intake, document critique, the review council, and output hygiene, plus the ship-a-draft wrapper. Installed automatically with every role pack.

`/plugin install core@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Turn rough notes into a structured brief, then get a verdict on the draft

Paste this into Claude Code:

```text
Here are my notes from today's planning call: <paste them>. Turn them into a brief, then critique the draft you write from it.
```

- **How to tell it worked:** brief-intake returns a structured brief with gaps tagged, and doc-critique ends with a verdict: SHIP IT, SHIP WITH CHANGES, MAJOR REWRITE or WRONG ARTIFACT.
- **If nothing happens:** If neither skill activates, check that `brief-intake/SKILL.md` and `doc-critique/SKILL.md` exist in your skills folder (`~/.claude/skills/` by default). In Claude Code, start a new session after installing.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `council-review`
- `doc-critique`
- `output-hygiene`

More: https://sananthanarayan.github.io/skilldrop/packs/core/
