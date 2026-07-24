---
rfc: 0003
title: Third-party catalogs (install --from)
status: implemented
date: 2026-07-24
author: sananthanarayan
---

# RFC-0003: Third-party catalogs (install --from)

## Problem / use case

`skilldrop-cli` installs only its bundled catalog — a store that sells its own goods. For skilldrop to be a package manager others publish through (the role agentbundle's catalogue channels play in agent-ready-repo), anyone must be able to author a repo of skills and have users install from it with the same one command, the same update path, and the same wiring files.

## Fit check

Structural change to the CLI only — no skill moves, no schema change for existing skills. The enabling insight: skilldrop's flat layout **is already the catalog contract**. Any directory or git repo containing `skills/<name>/` folders (each with `SKILL.md` + `manifest.json`, optionally a root `packs.json`) is a valid catalog — including this repo itself, which is just the bundled instance of the contract.

## Proposal

- **`--from <source>`** on `install` (and honored by `update`/`outdated`): a local directory path, or a git URL with optional `#ref` (branch/tag), shallow-cloned to a temp dir. Works with skill names, `--pack` (reads the catalog's own `packs.json`), and `--all`.
- **Ledger records provenance**: `.skilldrop.json` entries become `{version, source}`; `update`/`outdated` re-resolve each skill against its recorded source, so bundled and third-party skills update side by side. Legacy string entries are read as bundled.
- **Structural gate before copy**: each skill is checked (SKILL.md exists, manifest parses, name triple-match, description + model tier present) and refused with reasons on failure — a third-party catalog can't install broken folders.
- **Trust warning, always, for third-party sources**: skills are instructions an AI agent will follow; the CLI prints a review-before-use warning naming the installed paths. Install itself executes nothing — it only copies files.
- **`skilldrop validate [--from <source>]`**: the structural gate as a standalone command, so catalog authors can check their repo before publishing.

## Alternatives considered

- **A central registry index (npm-style)**: deferred — a curated index adds naming, squatting, and moderation problems; git URLs are decentralized, auditable, and enough for the ecosystem's current size. An index can layer on top later without breaking `--from`.
- **Tarball-URL sources**: deferred — adds download/extract machinery for little gain over git; `git` is present on every dev machine this tool targets.
- **Executing catalog-provided install hooks**: rejected outright — copy-only is the trust model.

## Decision

Implemented in `bin/skilldrop.js` (package version 0.2.0): `--from` with local-path and git`#ref` sources, provenance-aware ledger and updates, per-skill structural gate, trust warning, and the `validate` command. Catalog-authoring contract documented in README.
