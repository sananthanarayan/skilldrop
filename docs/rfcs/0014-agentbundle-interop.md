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

Adopt **Path C now, Path A never, Path B only on a real, sized request.** Path C step 1 is shipped
in this repo. The remaining recommendation steps, in priority order:

1. **[DONE] Path C, step 1** — skilldrop's own plugin marketplace + `npx skilldrop-cli` (this RFC).
2. **[TODO — his side, preferred] Ask for an agentbundle *source-adapter*.** agentbundle's whole
   design is "one adapter pipeline projects primitives into every layout." The reciprocal is a
   read-adapter for a skilldrop / agentskills.io-flat catalogue. Both tools already share the
   agentskills.io `SKILL.md` spec, so this is his codebase's job and costs skilldrop zero ongoing
   maintenance. Best outcome — pursue this first.
3. **[TODO — conditional] Path B: generate an agentbundle view.** Only if a real user base needs
   `agentbundle install` *and* he declines step 2. Blocked on two inputs from him: the published
   schemas for `.claude-plugin/plugin.json` and the full `marketplace.json` (the public docs
   reference but don't inline them), and rough agentbundle install numbers to justify the tax. If
   built: canonical source stays flat; a generator emits `packs/` + `pack.toml` + a
   `claude-plugins-dist` branch, pinned to a `minimum-agentbundle-version`, shipped as best-effort
   compatibility, not a support commitment.
4. **[TODO — optional] Per-pack Claude plugins.** Split the single catalogue plugin into one plugin
   per `packs.json` bundle via generated plugin directories (shares machinery with step 3).

Open verification before relying on the plugin path in anger:

- Confirm Claude Code's plugin agent loader **ignores `agents/README.md`** (it has no `name`/`description`
  frontmatter). If it errors instead of skipping, the fix is a generated plugin directory that excludes
  it (folds into step 4).
- Confirm a marketplace-root plugin with `source: "."` installs cleanly (marketplace.json and
  plugin.json coexisting in `.claude-plugin/`). Test with `/plugin marketplace add ./` from a clone.
