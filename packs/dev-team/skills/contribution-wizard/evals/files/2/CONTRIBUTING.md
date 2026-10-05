# Contributing to larkfield-agent-skills

Internal skills for the Larkfield Freight operations and billing teams. One folder per skill under `skills/`.

## What a skill folder contains

```
skills/<skill-name>/
  skill.yaml          # metadata, see below
  INSTRUCTIONS.md     # what the agent does
  tests/cases.yaml    # test cases
```

`<skill-name>` is lowercase kebab-case and matches `name` in `skill.yaml`.

## skill.yaml

All of these are required:

| field | notes |
|---|---|
| `name` | same as the folder |
| `summary` | one sentence, 160 characters or fewer |
| `owner` | a team listed in `OWNERS.md` — the team that answers when the skill is wrong |
| `category` | `billing`, `dispatch` or `claims` |
| `inputs` | list of what the user must supply |
| `related` | list of other skills in this repo (may be empty). Every entry must be a folder under `skills/` |
| `network` | `false` unless the security team has signed off |

## INSTRUCTIONS.md

Three sections, in this order: `## Purpose`, `## Steps`, `## Never`.
`## Never` lists at least two things the skill must not do.

## Tests

`tests/cases.yaml` needs at least 3 cases. Each case has `name`, `input` and `expect` (a list of things that must be true of the output).

## Catalogue

Add one row for the skill to `CATALOG.md`, in the table for its category, keeping the rows in alphabetical order.

## Before you open a pull request

Run `make check`. It validates every `skill.yaml`, checks that `related` entries exist and counts the test cases. A pull request with a failing `make check` is not reviewed.
