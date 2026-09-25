# CLAUDE.md

The substantive guidance for any agent working in this repo lives in [AGENTS.md](AGENTS.md) — repo overview, golden rules, file placement, voice & tone, and the pre-commit checklist. Read it first.

This file exists because Claude Code auto-loads `CLAUDE.md`. Everything below is **Claude-Code-specific** ergonomics that don't belong in the cross-IDE `AGENTS.md`.

## Dogfooding a skill while you build it

The fastest feedback loop for new or edited skills:

```bash
# user-scope: skill is available in every Claude Code session, no project pollution
mkdir -p ~/.claude/skills && cp -R skills/<skill-name> ~/.claude/skills/

# then in a new Claude Code session in any repo:
/<skill-name> <args>
```

For changes-in-flight, recopy after each edit — Claude Code reads `SKILL.md` fresh per invocation, but the copy in `~/.claude/skills/` is the one it sees, not the working tree.

## `${CLAUDE_SKILL_DIR}` semantics

Claude Code exports `CLAUDE_SKILL_DIR` to the absolute path of the installed skill folder when a skill runs. Use it in `SKILL.md` when telling the agent how to invoke a script:

```markdown
Run: `python3 ${CLAUDE_SKILL_DIR}/scripts/build_deck.py <args>`
(or, in non-Claude IDEs: `python3 skills/<skill-name>/scripts/build_deck.py <args>`)
```

Always show **both** forms — `${CLAUDE_SKILL_DIR}` for Claude Code, plain relative for Cursor / Continue / Cline / Aider. Hard-coding only one breaks portability, which is the whole point of skilldrop.

## Project settings

`.claude/settings.json` registers this repo as a **local plugin marketplace** so the catalogue can be dogfooded from the working tree without publishing:

```json
{
  "enabledPlugins": { "skilldrop@skilldrop-local": true },
  "extraKnownMarketplaces": {
    "skilldrop-local": { "source": { "source": "directory", "path": "." } }
  }
}
```

That means `/plugin` in a session opened at the repo root sees the skills, subagents, and loops as they exist on disk right now — edit a `SKILL.md` or a `LOOP.md` and the next invocation reads it, with no copy step. It is also the canonical place for any other Claude-Code-specific project config: hooks, permissions allowlists, or environment overrides.

## Sequencing belongs to a loop, never to a skill

**A skill never invokes another skill.** That rule is what keeps every skill independently
installable — one folder copied into Cursor or Aider works on its own, because nothing in it
assumes a sibling is present.

Sequencing lives one level up, in a **loop** (`loops/<name>/LOOP.md`, RFC-0028). A loop names
an ordered list of stages, the skills each stage runs, and the gate between them. It composes
skills by *ordering* them, not by having them call each other — so `build` can run
`feature-implement-loop` then `pre-merge-review` while both remain standalone skills.

- Need step B to follow step A? Add a stage to a loop, or write a new loop.
- Two skills genuinely need each other's internals? That's a signal to merge them, or to
  extract the shared logic into `reference.md`.
- Running a loop in Claude Code: read its `LOOP.md` and invoke each stage's skill yourself,
  honouring the gate between stages and the loop's `cap`. The loop is the script; you are the
  runner.
