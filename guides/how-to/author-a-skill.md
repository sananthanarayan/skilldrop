---
title: Author a new skill
summary: The short version of the authoring path — what a skill must contain, what gates it, and where the full contributor rules live.
kind: how-to
---

# Author a new skill

You can add a skill to the catalogue with every file the checks expect, and try it in another
repo before you open a pull request.

The lanes, PR gates and release flow are in [CONTRIBUTING.md](../../CONTRIBUTING.md); the rules
for each file are on [The skill contract](../reference/skill-contract.md).

## Write the RFC

A new skill starts with a one-page RFC that records the problem, the fit check and the
alternatives.

```bash
cp docs/rfcs/0000-template.md docs/rfcs/NNNN-<slug>.md
```

Fixes to an existing skill skip this.

## Scaffold the skill

Generate the folder in the one pack the skill belongs in; use `core` only if every role needs it.

```bash
node bin/skilldrop.js new-skill <your-skill> --pack <pack>
```

It writes `SKILL.md`, `manifest.json` and both eval files with every required section and
registers the skill in `model-routing.json`, so you replace the TODOs.

## Register and check the skill

Add a row to [Every skill, by category](../reference/skill-catalogue.md), the skill to an outcome
in `catalogue.json`, and a `CHANGELOG.md` bullet if it ships in a release, then run the lint.

```bash
python3 validate.py
```

It fails on a name, description or tier mismatch, a missing pack or outcome, and malformed evals.

## Try it in another repo

From inside the other repo, install the skill from your clone.

```bash
node ~/src/skilldrop/bin/skilldrop.js install <your-skill> --from ~/src/skilldrop --local
```

The skill is installed without touching that repo's git history.
