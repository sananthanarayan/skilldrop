---
title: Updates and the install ledger
summary: What outdated, update, diff and doctor compare and decide — the ledger file, how edited files become .upstream, every update flag, and the edge cases.
kind: reference
---

# Updates and the install ledger

This page lists the rules behind `outdated`, `update`, `diff` and `doctor`. For the task itself, see [Upgrade installed skills](../how-to/upgrade-skills.md). Loops are updated the same way as skills.

## The ledger

Each install directory holds a ledger, `.skilldrop.json`. When you install, it records:

- the version of each skill
- a hash of every file in it
- the catalogue commit it came from, pinned or not

`outdated` and `update` compare the ledger against the catalogue. After an update, the ledger records the new version and the new hashes.

## What `outdated` reports

`outdated` compares the version in your ledger with the latest in the catalogue. Changes nothing.

A catalogue can change a skill's files without bumping its version. The version check alone would never see that, so `outdated` compares the files too:

```text
example-skill: 1 file(s) changed in 'https://github.com/acme/skills' without a version bump (SKILL.md)
```

`--json` prints one JSON object on stdout and nothing else, for scripts and CI.

## What `update` does to each file

`update` re-copies every skill or loop whose version differs.

| Your copy | Catalogue copy | Result |
|---|---|---|
| Unedited (hash matches the ledger) | Changed | Replaced with the new version |
| Edited | Changed | Kept; the new version is written beside it as `<file>.upstream` |
| Edited | Unchanged | Left alone; no `.upstream` is written |
| Unedited | Removed | Deleted |
| Edited | Removed | Kept, and named in the output |

A kept edit is reported like this:

```text
updated runbook-generator 0.1.0 -> 0.2.0 (bundled)
  kept your edits in SKILL.md — new version at SKILL.md.upstream
```

Merge what you want from `SKILL.md.upstream` into `SKILL.md`, then delete the `.upstream` file.

Hook wiring is left in place.

## Edge cases

- **Unreachable source.** A skill whose source is unreachable is skipped with a warning; the run does not fail.
- **Third-party catalogues.** Skills from a third-party catalogue are run through the supply-chain scan again after they update.
- **Same version, different files.** `update` names these and doesn't take them. Read the change with `skilldrop diff <skill>`, then take it with `skilldrop update --changed`, which keeps your edits the same way as any update.
- **Pinned catalogues.** A skill installed with `--from <url>#<commit>` stays at that commit: `update` leaves it alone and says so. To move it, reinstall with the new commit.
- **Installs with no recorded hashes.** Skills installed before hashes were recorded have none. Their first update overwrites as `--force` does, then records hashes, so later updates keep your edits.

## Flags

| Flag | Applies to | What it does |
|---|---|---|
| `--dry-run` | `update` | Prints every decision `update` would make; writes nothing |
| `--changed` | `update` | Also takes files changed upstream under the same version |
| `--force` | `update` | Overwrites every file, including ones you edited |
| `--yes` | `update --force` | Skips the confirmation; scripts and CI are never asked |
| `--stat` | `diff` | The file list only, no line-level diff |
| `--json` | `outdated`, `doctor` | One JSON object on stdout, nothing else |
| `--project`, `--ide <name>`, `--dest <dir>`, `--local` | all four | The install target; pass the same one you installed with |

`--force` at a terminal lists the edited files first and asks before overwriting them.

## What `diff` shows

`skilldrop diff <name>` compares your copy of a skill or loop with the catalogue's, file by file. An installed loop is two files, `SKILL.md` (the catalogue's `LOOP.md`) and `loop.json`. It marks each changed file as your edit, a catalogue change, or both, then shows the line-level diff when git is on your PATH.

## What `doctor` checks

`doctor` compares the install directory with its ledger and reports:

- skills recorded but missing
- skills on disk that nothing recorded
- `.upstream` files waiting to be merged
- wiring or hooks left behind for skills that are gone

Each finding comes with the command that fixes it. `doctor` itself changes nothing.
