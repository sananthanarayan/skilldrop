# Skill engineering

For people writing Agent Skills in their own repos: write a portable SKILL.md folder from a described task, then audit any skill for routing, portability, safety, structure and evals before you share it.

`/plugin install skill-engineering@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Turn a task you keep explaining into a skill, then review it

Paste this into Claude Code:

```text
Make a skill that writes customer-facing release notes from the merged PRs I paste: grouped New / Improved / Fixed, breaking changes first, one line per PR with its number. We use Claude Code and Copilot, and we already have a launch-post skill for announcements. Then review the skill before I commit it.
```

- **Before you start:** A task you repeat with your coding agent, and Python 3.9 or later for the lint script
- **How to tell it worked:** skill-author writes a folder with SKILL.md, a template and evals, plus the install path for each of your tools, and skill-review returns a READY, FIX FIRST or REWRITE verdict with the lint script's output pasted in.
- **If nothing happens:** If a skill does not activate, ask for it by name ("use skill-author"). If the lint script will not run, check that python3 is on your PATH; skill-review can walk the same checks by hand.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `council-review`
- `doc-critique`
- `output-hygiene`
- `skill-author`
- `skill-review`

More: https://sananthanarayan.github.io/skilldrop/packs/skill-engineering/
