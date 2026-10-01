---
rfc: 0032
title: Pack landing pages, first-value metadata, and edit-preserving updates
status: accepted
date: 2026-10-01
author: sanjay-ananth
---

# RFC-0032: Pack landing pages, first-value metadata, and edit-preserving updates

## Problem / use case

A developer who finds skilldrop can install a pack in one command, but then gets stuck at two
points:

1. **After install, nothing says what to try first.** A pack in `packs.json` has a one-line
   description and a list of skills. There is no starter prompt, no description of what a good
   result looks like, and no page to land on. For example, a new `sre-oncall` user faces 6
   skills and no obvious first move.
2. **Updating erases their changes.** `skilldrop update` overwrites a skill wholesale
   ([`guides/how-to/upgrade-skills.md`](../../guides/how-to/upgrade-skills.md)). Adopters are
   encouraged to tailor skills to their codebase, and then lose those edits the first time
   they update.

agent-ready-repo solves both: each pack has a `[pack.first-value]` block (starter task and
prompt, how to verify, how to recover) with its own landing page, and an update writes
`<file>.upstream` instead of overwriting a file the user edited. These are the parts of its
pack model that help adopters. Its physical `packs/<p>/` layout is out of scope here (see
**Forward compatibility**).

## Fit check

Structural change: it touches the `packs.json` contract and CLI update behaviour.

- **Rule 2 (`skills/` stays flat)** is untouched. Packs remain metadata only (RFC-0001).
- **Zero runtime dependencies** is preserved. The metadata stays in JSON with no TOML parser,
  and the content hash uses Node's built-in `crypto`.
- **Portability** is unaffected. Nothing is added inside a skill folder, so a plain copy still
  works. The new metadata feeds the CLI, the site and the plugin output only.
- **Backwards compatibility:** every new field is optional, and a ledger entry with no hash
  updates exactly as it does today.

## Proposal

**1. Optional pack fields** in `packs.json` and `contracts/pack.schema.json`. The key names
are copied exactly from agent-ready-repo's `pack.toml`, so a later conversion is a direct
key-for-key copy:

```json
"sre-oncall": {
  "description": "…",
  "display_name": "SRE / on-call",
  "keywords": ["incident", "runbook", "slo"],
  "links": { "documentation": "https://…/packs/sre-oncall/" },
  "maintainers": [{ "name": "sanjay-ananth" }],
  "first-value": {
    "audience-posture": "technical",
    "prerequisites": [],
    "starter-task": "Turn an alert into a runbook an on-call can follow at 3am",
    "starter-prompt": "Write a runbook for the 'checkout p99 > 2s' alert on our payments service.",
    "verification": "A runbook exists with a triage step per symptom and a rollback section.",
    "recovery": "If the skill does not activate, run `skilldrop list` and confirm runbook-generator is installed."
  },
  "skills": ["…"], "loops": ["operate"]
}
```

`validate.py` checks the shape of every field. If a pack has a `first-value` block, its
`starter-prompt` must name, or clearly trigger, a skill or loop in that pack. All 7 packs ship
with `first-value` filled in.

**2. Per-pack landing pages.** `build_site.py` renders `/packs/<name>/` with the pack's
description, the starter task and prompt in a copy-paste block, how to verify and recover, its
loops, its skills grouped by outcome, and the one-line install command. `build_marketplace.py`
copies `display_name`, `keywords` and `links` into each plugin entry and writes a generated
`README.md` into each pack plugin on the `plugins` branch. A new `skilldrop info --pack <name>` form
prints the `first-value` block after install.

**3. Edit-preserving updates.** The ledger entry (`.skilldrop.json`) gains an optional `hash`
field: a SHA-256 of the installed files, recorded at install time. On `update`:

- If the files on disk still match `hash`, the skill is overwritten as today.
- If they differ, local edits are kept: each changed upstream file is written as
  `<file>.upstream` next to it, and the CLI prints which files need merging.
- `--force` keeps the current overwrite behaviour.
- A legacy entry with no `hash` behaves as today, then records a hash.

**Delivery order** (revised 2026-10-01, so pack-shaped content is written once):

1. **Part 3, edit-preserving updates**, first. It does not depend on pack shape, and it
   protects users' edits when skills later move.
2. **Pack re-cut** (RFC-0033): a `core` pack and one pack per skill, still in `packs.json`.
   Shipped in the same PR as step 1.
3. **Parts 1 and 2, first-value metadata and per-pack pages**, written for the re-cut packs.
4. **Physical migration** (RFC-0034) into `packs/<name>/`. Shipped in the same PR as step 3.

Each PR carries a CHANGELOG entry and a third-digit bump.
**Files touched:** `packs.json`, `contracts/pack.schema.json`, `validate.py`, `build_site.py`,
`build_docs.py`, `build_marketplace.py`, `bin/skilldrop.js`, `guides/how-to/upgrade-skills.md`,
README, and `llms.txt` (regenerated).

## Forward compatibility

The maintainer's stated direction is a later, full move to agent-ready-repo's physical layout.
That would be a separate RFC, and it would supersede the rejections in RFC-0001 and RFC-0014
Path A. This RFC is shaped so that move is cheap:

- **Field names** match `pack.toml`, so converting `packs.json` to `pack.toml` is a direct copy.
- **The CLI already reads the agentbundle shape** (`packs/<p>/.apm/skills`, RFC-0014), so a
  migrated catalogue stays installable with the current CLI.
- **The obstacle to physical nesting is known.** 12 skills belong to more than one pack
  (`brief-intake` and `doc-critique` are in three each; `council-review`, `output-hygiene`,
  `exec-summary`, `launch-readiness` and others are in two). The intended answer is a `core`
  pack, in the style of agent-ready-repo's `core` and `governance-extras`, for skills every
  role needs. The remaining
  role packs then get smaller and each skill has exactly one home. Those 12 are the starting
  candidate list, not a decision.

## Alternatives considered

- **Full physical migration now.** Rejected for now, not forever. It is an L-sized change of
  5–7 PRs. It breaks every `cp -R skills/<name>` instruction, the `--from` contract, ledger
  provenance and the `plugins` branch layout, and it needs the pack overlap redesigned first.
  The two gains in this RFC can ship without it.
- **Adopt `pack.toml` files alongside flat skills.** Rejected. It would add a TOML parser to a
  stdlib-only toolchain and split pack metadata across 7 files with no gain over one JSON file
  until skills actually move.
- **Per-pack versioning.** Rejected. Per-skill versions let `outdated` report each skill
  separately, and a single pack version would hide which skill changed.
- **Do nothing.** Rejected. The first-run gap and lost edits are the two largest barriers to
  adoption, and both can be fixed without breaking anything.

## Decision

Accepted 2026-10-01. Delivery follows in separate PRs.
