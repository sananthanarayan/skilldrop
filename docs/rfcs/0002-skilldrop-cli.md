---
rfc: 0002
title: skilldrop CLI — npm-distributed installer (MVP)
status: implemented
date: 2026-07-24
author: sananthanarayan
---

# RFC-0002: skilldrop CLI — npm-distributed installer (MVP)

## Problem / use case

The repo's skills are meant to be used from Claude Code, Cursor, Kiro, Codex, Continue, Cline, and Aider — but today consumption requires cloning the repo and running `cp -R` per skill (or `pack.py` per pack), plus hand-writing the wiring files Cursor and Kiro need. There is no update path at all: a user who copied a skill in June never learns it improved in July. Distribution is the product's last mile and it's manual.

## Fit check

Structural change — adds `package.json` and `bin/` at the repo root (new top-level files need an RFC). Golden rules hold: `skills/` doesn't move, per-skill `cp -R` and `pack.py` keep working, and the CLI performs **copy, not projection** — the installed artifact is byte-identical to the repo folder, preserving the portability premise. The full command surface was already designed in `skilldrop-cli-design/skilldrop-cli-design.md`; this RFC scopes the MVP and corrects one fact: **`skilldrop` is taken on npm**, so the package is **`skilldrop-cli`** (the bin command remains `skilldrop`).

## Proposal

Make the repo itself the npm package: root `package.json` (name `skilldrop-cli`, `files`: `skills/`, `packs.json`, `model-routing.json`, `bin/`) with a single-file, zero-dependency Node CLI at `bin/skilldrop.js`. Skills ship inside the package, so `npx skilldrop-cli …` works offline after fetch and versions are pinned by npm.

MVP commands:

- `list` / `info <skill>` / `packs` — catalog, per-skill detail (version, tier, related, packs), pack listing
- `install <skill…> | --pack <name> | --all` with `--with-related`, targeting `--ide claude` (default; `--project` for repo scope), `--ide cursor` (writes the `.cursor/rules/<skill>.mdc` rule file), `--ide kiro` (writes the `.kiro/steering/<skill>.md` steering file), or `--dest <dir>` for everything else (Codex, Continue, Cline, Aider — wiring guidance printed, per README)
- `update` / `outdated` / `uninstall <skill>` — a `.skilldrop.json` ledger in each install destination records name→version; update/outdated diff it against the shipped catalog; uninstall also removes the wiring file it wrote
- Dependency notes: any installed skill with `requirements.txt` prints its pip install line

Deferred (fast-follows, per the design doc): `search`, `doctor`, IDE auto-detection, version pinning `@<version>`, `--ide all`.

## Alternatives considered

- **agentbundle-style projection engine:** rejected — skilldrop skills need no per-IDE transformation; a projection layer would add the complexity the repo exists to avoid.
- **Fetch-from-GitHub at runtime instead of bundling:** rejected for MVP — bundling gives offline installs, npm-pinned versions, and no rate limits; the registry-refresh model can come with the update-channel fast-follow.
- **Publish under a scope (`@handle/skilldrop`):** viable fallback; `skilldrop-cli` is free and unscoped installs are friendlier for `npx`.

## Decision

Implemented as proposed: `package.json` + `bin/skilldrop.js` at the repo root, README gains the npx path, CLI design doc updated (name correction + MVP status). Publishing (`npm publish`) is a maintainer step outside the repo.
