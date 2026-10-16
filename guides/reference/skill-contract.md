---
title: The skill contract
summary: What a new skill folder must contain — frontmatter, manifest, size, scripts, evals, catalogue entries — and what validate.py checks before it merges.
kind: reference
---

# The skill contract

This page is the detail behind [Author a new skill](../how-to/author-a-skill.md). The full
contributor guide — the three lanes, the PR gates and the release flow — is in
[CONTRIBUTING.md](../../CONTRIBUTING.md), and the authoritative checklist is in
[AGENTS.md](../../AGENTS.md).

## The RFC

New skills and structural changes need a one-page RFC: copy
[`docs/rfcs/0000-template.md`](../../docs/rfcs/0000-template.md) to `docs/rfcs/NNNN-<slug>.md`
and record the problem, the fit check and the alternatives. Fixes to existing skills don't need
one.

## What the scaffold does

`node bin/skilldrop.js new-skill <your-skill> --pack <pack>` writes `SKILL.md`, `manifest.json`
and both eval files with every required section, and registers the skill in
`model-routing.json`. Replace the TODOs; the rules below are what it sets up for you, and the
catalogue entries after them are still yours to add.

## Folder and pack

The skill lives in the one pack it belongs in (`core` only if every role needs it), at
`packs/<pack>/skills/<your-skill>/`. Its pack is set by that folder.

## `SKILL.md`

Frontmatter:

```yaml
---
name: your-skill
description: One sentence, use-case-first. AI agents match this against user prompts to decide when to invoke.
---
```

Keep `SKILL.md` short (under ~500 lines). Move long reference material into sibling files such as
`reference.md`, `examples.md` or `templates/`.

## `manifest.json`

It sits beside `SKILL.md` with the same `name` + `description`, plus declared `deps` and required
env vars. This is what makes the skill portable across IDEs.

## Scripts

A skill with scripts declares what they do in `manifest.json` `permissions`: hosts contacted,
programs run, and where files are written (see [AGENTS.md](../../AGENTS.md)). The scripts go in
`scripts/` and are referenced with a path relative to the skill folder. Don't hard-code
`${CLAUDE_SKILL_DIR}` alone; show both paths so non–Claude-Code users aren't stuck.

## Evals

An `evals/` folder is required; `validate.py` fails a skill without it.

- `evals.json` — at least one realistic prompt with a list of assertions the output must satisfy.
- `eval_queries.json` — phrases that should and should **not** trigger the skill.

They double as the checklist for the manual test pass and keep the `description` honest about
when the skill fires.

## Catalogue entries

- A row in [Every skill, by category](skill-catalogue.md), and in **Installing dependencies** in
  [Install a skill into your IDE](../how-to/install-per-ide.md) if the skill has runtime deps.
- At least one outcome in `catalogue.json`.
- A bullet in [`CHANGELOG.md`](../../CHANGELOG.md) under the new version, if the change is going
  out in a release. The site build fails without one.

## What `validate.py` checks

Run `python3 validate.py` from the repo root. It checks name consistency, the tier sync with
`model-routing.json`, the `related`↔SKILL.md reference sync, description sync, pack and outcome
membership, and eval file shape.

## Trying it in another repo

From inside the other repo, `node ~/src/skilldrop/bin/skilldrop.js install <your-skill> --from ~/src/skilldrop --local`
installs the skill without touching that repo's git history; both paths point at your clone.
