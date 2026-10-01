---
title: Upgrade installed skills
summary: Check which installed skills are stale and bring them current, keeping any files you edited and your hook wiring.
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

- **Files you edited are kept.** When you install a skill, the ledger (`.skilldrop.json`) records a hash of every file in it. On update, a file whose hash still matches is replaced with the new version. A file you changed is left alone, and the new version is written next to it as `<file>.upstream`:

  ```
  updated runbook-generator 0.1.0 -> 0.2.0 (bundled)
    kept your edits in SKILL.md — new version at SKILL.md.upstream
  ```

  Merge what you want from `SKILL.md.upstream` into `SKILL.md`, then delete the `.upstream` file. If the catalogue didn't change a file you edited, update leaves it alone and writes no `.upstream`.
- **Files the catalogue removed** are deleted only if you never edited them. An edited one is kept and named in the output.
- **Hook wiring** is left in place.
- The ledger is updated to record the new version and the new hashes.

## Take every new version anyway

```bash
npx skilldrop-cli update --force
```

`--force` overwrites every file, including ones you edited. Skills installed before this feature have no recorded hashes. Their first update overwrites as `--force` does, then records hashes, so later updates keep your edits.
