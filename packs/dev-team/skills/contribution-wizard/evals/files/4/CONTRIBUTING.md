# Contributing a skill

Harrowgate University Library, Systems & Discovery team. Last revised 12 March 2026.

Skills are short instruction files our staff assistant loads when a member of staff
asks for a particular job. Six of us maintain them. Keep them small.

## Layout

Each skill is one folder under `skills/`:

```
skills/<name>/
  skill.toml            metadata
  PROMPT.md             the instructions the assistant follows
  examples/
    01-input.md         what a member of staff would paste
    01-expected.md      what a good answer looks like
    02-input.md
    ...
```

At least three input/expected pairs. One of them must be an awkward case (missing
field, contradictory request, nothing to do).

Since March 2026 metadata lives in `skill.toml`. A few older skills still carry a
`meta.json` until someone migrates them. New skills must not add one.

## skill.toml

```toml
name = "summarise-reading-list"      # same as the folder name
summary = "One sentence, 120 characters at most."
category = "cataloguing"             # one of the categories in registry.json
maintainer = "alias@harrowgate.example"
handles_patron_data = false
version = "0.1.0"                    # new skills start at 0.1.0
```

## Naming

- lowercase, words joined with hyphens
- starts with a verb (`summarise-`, `flag-`, `draft-`)
- no abbreviations a new member of staff would not know. Write `interlibrary-loan`,
  not `ill`; write `reading-list`, not `rl`.
- 40 characters at most

## Patron data

If the input a skill receives can contain patron names, library card numbers or
contact details, set `handles_patron_data = true`, and PROMPT.md must tell the
assistant never to repeat a library card number in its output (refer to the patron
by name or by request number instead).

## Registry

Add one entry for the skill to the `skills` list in `registry.json` (name, category,
maintainer). Keep the list in alphabetical order by name.

## Before you open a pull request

Run `python3 tools/lint_skills.py` from the repo root. It checks the layout, the
naming rules and that every skill is in the registry.
