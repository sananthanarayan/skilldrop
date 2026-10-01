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

## See what would change first

```bash
npx skilldrop-cli update --dry-run      # every decision update would make, nothing written
npx skilldrop-cli diff runbook-generator   # your copy against the catalogue's, file by file
```

`diff` marks each changed file as your edit, a catalogue change, or both, then shows the
line-level diff when git is on your PATH (`--stat` for the file list only).

## Update all outdated skills

```bash
npx skilldrop-cli update
```

Re-copies every skill whose version differs. Skills whose source is unreachable are skipped with a warning rather than failing the run. Skills from a third-party catalogue are run through the supply-chain scan again after they update.

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

`--force` overwrites every file, including ones you edited. At a terminal it lists the edited files first and asks before overwriting them; `--yes` skips the question, and scripts and CI are never asked. Skills installed before this feature have no recorded hashes. Their first update overwrites as `--force` does, then records hashes, so later updates keep your edits.

## Check an install is healthy

```bash
npx skilldrop-cli doctor
```

Compares the install directory with its ledger and reports skills recorded but missing,
skills on disk that nothing recorded, `.upstream` files waiting to be merged, and wiring or
hooks left behind for skills that are gone. Each finding comes with the command that fixes it.
`doctor` itself changes nothing.

## Same version, different files

A catalogue can change a skill's files without bumping its version. The version check alone
would never see that, so `outdated` compares the files too:

```text
example-skill: 1 file(s) changed in 'https://github.com/acme/skills' without a version bump (SKILL.md)
```

`update` names these and doesn't take them. Read the change with `skilldrop diff <skill>`, then
take it with `skilldrop update --changed`, which keeps your edits the same way as any update.

## Pinned catalogues

A skill installed with `--from <url>#<commit>` stays at that commit: `update` leaves it alone
and says so. To move it, reinstall with the new commit. Every install records the commit it
came from in `.skilldrop.json`, pinned or not.

