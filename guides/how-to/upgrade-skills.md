---
title: Upgrade installed skills
summary: Check which installed skills and loops are stale and bring them current, keeping any files you edited and your hook wiring.
kind: how-to
---

# Upgrade installed skills

You can see which installed skills and loops are behind the catalogue and bring them current without losing the files you edited.

This works on anything you installed with `skilldrop install`; no extra pack is needed. Loops are updated the same way as skills. Every rule, flag and message is on [Updates and the install ledger](../reference/update-and-ledger.md).

## See what is outdated

Start by listing what is behind.

```bash
npx skilldrop-cli outdated
```

It compares each installed version with the catalogue's, names files that changed without a version bump, and changes nothing.

## Preview the update

Check every decision before anything is written.

```bash
npx skilldrop-cli update --dry-run
```

It prints what `update` would replace, keep or skip. To read one skill's changes file by file, run `npx skilldrop-cli diff <skill>`.

## Update everything

Bring every outdated skill and loop current.

```bash
npx skilldrop-cli update
```

Files you never touched are replaced. A file you edited is kept, and the new version is written beside it as `<file>.upstream`. Hook wiring stays in place.

## Merge the new versions into your edits

Find the `.upstream` files the update left.

```bash
npx skilldrop-cli doctor
```

It lists each `.upstream` file waiting to be merged; copy what you want into your file, then delete the `.upstream` one.

## Update a project-scope install

Pass the target flag you installed with, to `outdated` as well as `update`.

```bash
npx skilldrop-cli update --project
```

It updates `./.claude/skills` instead of the user-scope folder.

## Take changes made without a version bump

Read the change with `diff` first, then take it.

```bash
npx skilldrop-cli update --changed
```

It takes files the catalogue changed under the same version, and keeps your edits as any update does.

## Overwrite your edits

Take every new version when you no longer want your changes.

```bash
npx skilldrop-cli update --force
```

It overwrites every file, including ones you edited. At a terminal it lists those files and asks first.
