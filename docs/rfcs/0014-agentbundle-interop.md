---
rfc: 0014
title: Interop with the agentbundle ecosystem
status: accepted   # draft → accepted | rejected → implemented
date: 2026-07-28
author: sananthanarayan
---

# RFC-0014: Interop with the agentbundle ecosystem

## Problem / use case

The author of [`agent-ready-repo`](https://github.com/eugenelim/agent-ready-repo) — which
ships the `agentbundle` package manager (`pip install agentbundle`) — asked that people who
use agentbundle be able to install packs from skilldrop's catalogue. His opening ask was that
skilldrop **rework entirely** into agentbundle's format. That does not make sense: it would
delete skilldrop's identity (flat `skills/<name>` + virtual packs + copy-install, golden rules
1–3) to become a downstream folder of a competing installer, for zero benefit to skilldrop's
own users. The real, narrow goal is **one-directional interop**: agentbundle (and Claude Code)
users can install skilldrop's catalogue, while skilldrop stays skilldrop and keeps `skilldrop-cli`
as its primary rail.

## Fit check (structural change)

Golden rules touched, and why they hold:

- **Skills are discovered by path; they stay flat in `skills/<name>` (GR1).** Not broken — no
  skill moves. The shipped step (below) exposes the existing flat `skills/` and `agents/` trees
  as a single Claude Code plugin whose source is the repo root (`"."`); nothing is copied or
  projected into per-pack directories.
- **Copy-install, never transform on the way in (GR2).** Preserved — the plugin path is Claude's
  own copy-to-cache install of the same folders; no build-time projection of skill bodies.
- **No duplicated strings (the validate.py discipline).** Preserved — `.claude-plugin/{marketplace,
  plugin}.json` are generated from `package.json` by `build_marketplace.py`, and `validate.py`
  fails on drift, exactly as `build_site.py` / manifests are guarded today.

## Proposal

Three paths were weighed against the goal:

- **Path A — adopt agentbundle as skilldrop's format** (physical `packs/<name>/.apm/…`, `pack.toml`,
  `.claude-plugin/plugin.json` per pack, their projection build). **Rejected** — reverses RFC-0001
  (physical packs), couples the repo to an external, evolving schema, and retires `skilldrop-cli`.
- **Path B — generate an agentbundle-compatible view from skilldrop's flat source** (a build script
  emits `packs/` + `pack.toml` + `marketplace.json` to a `claude-plugins-dist` branch; canonical
  source stays flat). **Deferred, conditional** — this is the only path that satisfies `agentbundle
  install` specifically, but it is a permanent schema-chasing tax to serve a competing tool's users.
- **Path C — own skilldrop's install rails** (`npx skilldrop-cli`, already shipped; plus skilldrop's
  *own* `.claude-plugin/marketplace.json`). **Shipped now.** The marketplace.json format is a Claude
  Code standard, not agentbundle-specific, so it unlocks `/plugin marketplace add sananthanarayan/skilldrop`
  independently of agentbundle, and produces roughly half of Path B's artifacts as a byproduct.

Shipped in this RFC (Path C, step 1):

- `build_marketplace.py` — generator + `--check`, single-sourced from `package.json`.
- `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json` — the catalogue as one plugin,
  `source: "."`, install as `skilldrop@skilldrop`; skills invoke as `/skilldrop:<name>`.
- `validate.py` drift guard (imports `build_marketplace.stale()`), so the existing CI lint fails on
  a stale committed file.
- `author` field added to `package.json` (single source for owner/author across npm and the plugin).
- README "Or: the Claude Code plugin marketplace" install path.

Anti-patterns this bans: (1) hand-editing `.claude-plugin/*.json` (drift-guarded — regenerate);
(2) reworking skilldrop into agentbundle's on-disk shape (Path A).

## Alternatives considered

- **Do nothing / point people at `--from <git-url>`.** Loses — it serves neither agentbundle users
  (wrong tool) nor Claude Code plugin users (no marketplace file), which is precisely the ask.
- **Per-pack Claude plugins now** (one plugin per `packs.json` bundle). Loses for *step 1* — Claude
  copies each plugin dir to cache and can't reference files outside it, so per-pack plugins need
  generated plugin directories on a dist branch. That is real generation, overlapping Path B, and is
  deferred rather than rushed.

## Decision

Adopt **Path C now, Path A never, Path B via a generated view.** The clarified ask is *shared
schema, bidirectional, no code coupling* — agentbundle can set skilldrop as a catalogue source and
vice versa. Two findings unblock this:

- **His `contracts/` are standalone, versioned JSON Schemas** (`pack.schema.json`,
  `catalogue.schema.json`, `plugin-manifest.schema.json`, `skill.schema.json`, …; `schema = 1`,
  adapter-contract v0.14). So conformance is pinning a *version*, not tracking his HEAD — the honest
  form of "no coupling." The skill layer is already identical (both use the agentskills.io `SKILL.md`
  spec: `name` + `description`). Manifest floors are tiny (`pack.toml` needs `[pack]` name/version/
  description + `[pack.install] default-scope`; `plugin.json` needs name/version/description).
- **PyPI is a non-issue.** A catalogue is a *git repo*, read from a `git+https://` URL; agentbundle
  (the tool) is on PyPI, the catalogue is not. skilldrop-cli stays on npm; nothing publishes to PyPI.

The only real gap is on-disk layout (his physical `packs/<name>/.apm/skills/…` vs skilldrop's flat
`skills/` with multi-pack membership), which a generator resolves by duplicating a shared skill into
each generated pack — something native adoption can't do without breaking RFC-0001. Steps, in order:

1. **[DONE] Path C** — skilldrop's own plugin marketplace + `npx skilldrop-cli` (`build_marketplace.py`).
2. **[DONE] Path B generator** — `build_catalogue.py` renders the his-schema catalogue from flat
   source into `dist/` (gitignored): `catalogue.toml`, `.claude-plugin/marketplace.json`, and
   `packs/<pack>/{pack.toml, .claude-plugin/plugin.json, .apm/skills/<skill>/…}`, one plugin per
   `packs.json` bundle. Contract knobs pinned in-file (`ADAPTER_CONTRACT`, `MIN_AGENTBUNDLE`). `--check`
   is a stdlib pre-flight on required fields; `agentbundle validate` is authoritative.
3. **[DONE] Publish `dist/` to the `agentbundle-catalogue` branch in CI** —
   `.github/workflows/agentbundle-catalogue.yml` regenerates on every push to main and
   force-pushes an orphan commit rooted at `dist/`, so
   `agentbundle install --pack <p> git+https://github.com/sananthanarayan/skilldrop@agentbundle-catalogue`
   resolves (agentbundle pins a git ref with `@`, not `#`). Separate workflow (never touches the
   npm publish path), `contents: write` only.
4. **[DONE] Reverse direction** — `skilldrop-cli --from` reads an agentbundle catalogue
   (`packs/<name>/{pack.toml,.apm/skills/<skill>/SKILL.md,.apm/agents/…}`) via an `apm`-shape
   reader in `bin/skilldrop.js` that normalizes it onto the native accessors (skill list, virtual
   packs from each `pack.toml`, synthesized manifests, agents). Verified end-to-end against
   agent-ready-repo: `skilldrop install --pack contracts --from git+…/agent-ready-repo` installs his
   `api-contract`/`event-contract`. Additive to the npm CLI, no coupling.
5. **[DECLINED — his call, 2026-07-29] Flat-catalogue source-adapter / neutral shared spec.**
   Asked the agent-ready-repo owner to (a) add an agentbundle source-adapter that reads a flat
   agentskills.io catalogue directly (which would have retired step 3's generated view) and (b)
   relax the `.apm/` wrapper. He declined both: **`.apm/` is mandatory**, a flat catalogue "does
   not work for various reasons," and these asks "don't make sense for the ecosystem view." So this
   is not co-owned bidirectional interop — it is **skilldrop conforming to his ecosystem contract via
   the generated export**, one-directional, permanent. Consequence: the `agentbundle-catalogue` branch
   (step 3) is standing, not a temporary bridge. No code impact — our generator already emits `.apm/`,
   the exact point he requires.
6. **[DONE — 2026-07-30] The consolidating contract landed (RFC-0076, adapter-contract v0.17) with a
   real verifier; aligned `catalogue.toml` to it.** agent-ready-repo now ships two schema-backed
   conformance tools: `agentbundle catalogue verify --root <local-checkout>` (whole catalogue, an 18-step
   pipeline that builds into a tmpdir and validates each `pack.toml`/generated `plugin.json` against the
   `contracts/` schemas) and `agentbundle validate <pack-dir>` (one pack). Both validate against the
   schemas the *installed CLI version* bundles — pin by pinning the `agentbundle` version, not by
   vendoring. Findings and fixes:
   - `catalogue.schema.json` is `additionalProperties:false` and requires far more than we emitted:
     `[catalogue]` needs `paths`+`build`+`package`; `[catalogue.paths]` needs `profiles`+`build-output`;
     `[catalogue.build]` (`recipes`,`self-host`,`claude-plugin-branch`,`marketplace-description`) and
     `[catalogue.package].include` and `[distribution.agentbundle.artifactory].enabled` were entirely
     missing. `build_catalogue.py` now emits the full shape (the build/package/artifactory values are
     inert for us but must be present + valid; `preferred-adapter` must name a real adapter → `claude-code`).
   - `pack.toml` (`[pack]` requires only name/version), `plugin.json` (name/version/description, and must
     match the pack's name/version), and `SKILL.md` frontmatter (name/description only — audited: all 50
     skills conform to the allow-list) were already valid.
   - Contract version: `0.14` still conforms (the spec gate refuses only on a *major* mismatch, and both
     are major-0), but bumped `ADAPTER_CONTRACT` to `0.17` for currency; `MIN_AGENTBUNDLE` stays `0.13.0`
     (shape-checked only for git sources). The new optional `[[pack.integrations]]` (RFC-0076 D6) is not
     emitted.
   - There is **no** `export-contract` / `agentbundle catalogue contracts` command (RFC-0076 D5 not landed),
     and `verify` has **no git-URL mode** — verification is `--root` against a local checkout of the branch.
7. **[TODO — optional] Gate CI on `agentbundle catalogue verify`** — needs the Python `agentbundle[lint]`
   tool in the workflow (not stdlib), so it's a heavier CI addition than the current stdlib `--check`.
8. **[TODO — optional] Per-pack agents** — map reviewer subagents into the packs' `.apm/agents/`.

Never Path A (native restructure into physical packs — breaks multi-pack membership + RFC-0001).

**Status (2026-07-30): conformant to the landed contract; awaiting a live `agentbundle catalogue verify`.**
Two-way interop works (generated branch out, `apm` reader in) and `catalogue.toml` now matches the current
schema. Not yet run through the real verifier — that needs `pip install agentbundle[lint]` + a local checkout
(the tool isn't in this repo). Open question for the maintainer: the generated branch is a permanent
re-alignment tax whenever his contract shifts — worth confirming the agentbundle install base justifies it.

Open verification before relying on the plugin path in anger:

- Confirm Claude Code's plugin agent loader **ignores `agents/README.md`** (it has no `name`/`description`
  frontmatter). If it errors instead of skipping, the fix is a generated plugin directory that excludes
  it (folds into step 4).
- Confirm a marketplace-root plugin with `source: "."` installs cleanly (marketplace.json and
  plugin.json coexisting in `.claude-plugin/`). Test with `/plugin marketplace add ./` from a clone.
