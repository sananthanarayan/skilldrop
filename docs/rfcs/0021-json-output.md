---
rfc: 0021
title: Machine-readable --json output for the read commands
status: implemented
date: 2026-08-06
author: sananthanarayan
---

# RFC-0021: Machine-readable `--json` output for the read commands

## Problem / use case

A comparison against `luongnv89/asm` (a universal skill manager indexing 4,394 skills across 54
repos) surfaced a gap: every ASM command supports `--json` and `--yes` for non-interactive
automation, marketed as "agent-ready". `skilldrop-cli`'s read commands print **human-aligned
columns only** — an agent, script, or CI job wanting the catalog has to scrape padded text, and
`skilldrop info <skill>` can't be consumed programmatically at all.

That matters more than a nicety: skills are increasingly consumed *by agents*, and skilldrop's own
`model-router` pattern assumes a program can ask "what tier is this skill?" without parsing prose.
The catalog data already exists as structured JSON on disk (`manifest.json`, `packs.json`,
`model-routing.json`) — the CLI was throwing that structure away at the print boundary.

## Fit check (structural change)

Golden rules touched, and why they hold:

- **"Never invent commands or file conventions."** No new command and no new file — `--json` is an
  additive flag on five existing read commands (`list`, `info`, `packs`, `agents`, `outdated`).
- **Human output is unchanged.** Default behaviour is byte-identical; `--json` is opt-in, so no
  existing script or doc breaks.
- **Zero dependencies preserved.** `JSON.stringify` only.
- **CLI public surface changes** (a new flag) → a **minor** version bump per AGENTS.md.

## Proposal

Add `--json` to the five read commands. Each emits **one JSON object on stdout and nothing else**
(errors still go to stderr with a non-zero exit), via a single `emitJSON()` helper:

- `list --json` → `{catalog, count, skills:[{name, version, tier}]}`
- `info <skill> --json` → `{catalog, name, version, description, tier, packs, related, tags, deps:{pip,npm,requirementsTxt}, env:{required,optional}, hooks}`
- `packs --json` → `{catalog, count, packs:[{name, description, skills}]}`
- `agents --json` → `{catalog, count, agents:[{name, description, tools, model}]}`
- `outdated --json` → `{dest, count, outdatedCount, skills:[{name, installed, current, source, outdated}]}`

Works with `--from` (third-party catalogs) and the install-target flags, exactly as the human forms
do. `outdated --json` deliberately reports *all* installed skills with an `outdated` boolean (not
just the stale ones) so a consumer gets the full inventory in one call.

Anti-patterns this bans: mixing human log lines into `--json` output; a `--json` mode that omits
data the human form shows.

## Alternatives considered

- **A separate `skilldrop export` command.** Rejected — a second command surface for the same data,
  and it wouldn't compose with `--from` / target flags for free.
- **`--format json|table`.** Rejected — more surface than the problem needs; `--json` is the
  ecosystem convention (ASM, `gh`, `npm`).
- **Emit JSON for write commands too (`install`/`update`).** Deferred — those are progress streams,
  not queries; a structured result object for them is a separate design (and `--yes`-style
  non-interactive install is a bigger question).
- **Do nothing.** Rejected — agents are a first-class consumer now; scraping padded columns is a
  defect, not a style preference.

## Decision

Accepted and implemented in `bin/skilldrop.js` — all five read commands take `--json`, verified to
emit valid parseable JSON with human output unchanged. Ships as a **minor** release (new CLI flag).
