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

`.claude/settings.json` exists at the repo root and is currently empty (`{}`). It's the canonical place to add Claude-Code-specific configuration scoped to this project — hooks, permissions allowlists, `enabledPlugins`, `extraKnownMarketplaces`, or environment overrides. Add config when you have something concrete to configure; an empty file is honest about the current state.

## When NOT to use a skill

Don't invoke a skilldrop skill from inside another skilldrop skill. Skills are designed to compose at the human's invocation layer (e.g. user runs `brief-intake` then hands the brief to `adr-generator`), not via internal chaining. If two skills genuinely need to call each other, that's a signal to merge them or to extract shared logic into `reference.md`.
