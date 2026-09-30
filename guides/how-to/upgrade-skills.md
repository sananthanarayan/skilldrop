---
title: Upgrade installed skills
summary: Check which installed skills are stale and bring them current without clobbering your settings or hook wiring.
kind: how-to
---

# Upgrade installed skills

Skills improve over time — descriptions sharpen, anti-patterns get named, model-tier hints get tuned. This guide shows how to see what is stale and bring everything current.

## See what is outdated

```bash
npx skilldrop-cli outdated
```

Compares the version in your ledger (`.skilldrop.json` in the install directory) against the latest in the catalogue. Does not change anything.

## Update all outdated skills

```bash
npx skilldrop-cli update
```

Re-copies every skill whose version differs. Skills whose source is unreachable are skipped with a warning rather than failing the run.

## Project-scope installs

Pass the same flag you used at install time:

```bash
npx skilldrop-cli outdated --project
npx skilldrop-cli update --project
```

## What update preserves

- The ledger (`.skilldrop.json`) is updated to record the new version
- Hook wiring is left in place — `update` only re-copies the skill folder
- Any customisations you made inside the installed skill folder are overwritten

Copy local edits out before updating.
