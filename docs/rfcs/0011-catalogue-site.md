---
rfc: 0011
title: Catalogue site on GitHub Pages
status: draft
date: 2026-07-26
author: sananthanarayan
---

# RFC-0011: Catalogue site on GitHub Pages

## Problem / use case

skilldrop is 49 skills, 6 packs, 229 distinct tags, three model tiers, and a `related` graph connecting them. The only way to browse that today is scrolling one README table, which cannot filter, cannot be linked to a single skill, and does not show a skill's tier, pack membership, or companions without opening `manifest.json`.

Two concrete consequences:

- **Discovery is worst exactly when the catalogue is most useful.** Someone who knows they want an ADR generator finds it. Someone who has an incident and doesn't know `postmortem-generator`, `runbook-generator`, and `incident-comms` exist reads a wall of prose or gives up.
- **It leaves an open question open.** [`skilldrop-cli-design.md:296`](../designs/skilldrop-cli-design.md) asks "what's the official registry URL? GitHub Pages on this repo? A `skilldrop.dev` site?" and defers it to v2. Third-party catalogs shipped in [RFC-0003](0003-third-party-catalogs.md) — a browsable index is more useful now than it was when that question was written.

The target URL is **`https://sananthanarayan.github.io/skilldrop/`** (project pages, base path `/skilldrop/`).

## Fit check

Structural change — a new top-level directory and a new workflow. Touches golden rules 2 and 4:

- **Rule 2 (`skills/` doesn't move):** upheld. The site is generated *from* `skills/`; nothing moves, and no skill gains a file.
- **Rule 4 (never invent commands or conventions):** the risk. Every fact on the site must come from `manifest.json`, `packs.json`, or `model-routing.json` — never hand-typed. A description already exists in two places (`SKILL.md` frontmatter and `manifest.json`) and `validate.py` fails on drift between them; a hand-written catalogue page would be an unchecked third copy. **The page is generated, and `validate.py` gains a staleness check.** This is the load-bearing constraint of the whole RFC.

## The choice this RFC exists to settle

agent-ready-repo's site is two static-site generators feeding one artifact:

| Piece | Their tooling | Output |
|---|---|---|
| Marketing landing | Astro (TypeScript, npm, Node 24) in `web/` | `build/` |
| Reference docs | Material for MkDocs (pip) in `site/` | `build/docs/` |
| Catalogue content | `tools/build-site.py` generating from pack manifests | consumed by MkDocs |
| Deploy | `pages.yml` → `upload-pages-artifact@v3` on `./build` → `deploy-pages@v4` | |

Astro runs first because it cleans `build/` on every run.

**Their information architecture is right and worth copying.** Landing → catalogue → docs, one `build/` directory, one artifact, one workflow, deploy on `main` only. That structure is proposed below verbatim.

**Their toolchain is the open question**, because skilldrop's constraints differ: `validate.py` is stdlib-only on purpose, `bin/skilldrop.js` is zero-dependency, and the repo's premise is that a skill is a folder you copy. Adding Astro + MkDocs + Node 24 + Python 3.12 would make the site's build stack larger than the tool it documents.

### Option A — generated static HTML, no SSG (recommended)

- `build_site.py` at the repo root, **stdlib only**, matching `validate.py`'s convention. Reads `skills/*/manifest.json`, `packs.json`, `model-routing.json`. Emits `build/index.html`: the full catalogue with client-side filtering by pack, tag, and tier, plus text search, plus each skill's `related` companions as links.
- One hand-written page shell; all 49 entries generated. No npm, no pip, no lockfile.
- Docs stay on GitHub (11 RFCs, 3 design docs — they render with working relative links today) and the site links to them.
- `pages.yml` runs `python3 build_site.py`, uploads `./build`.

**Cost:** no rendered markdown on the site, so RFCs live at github.com rather than under `/skilldrop/docs/`.

### Option B — Option A plus Material for MkDocs for `docs/`

Adds `site/mkdocs.yml` + `site/requirements.txt`, builds RFCs and design docs to `build/docs/`. Their exact docs half. Adds a pip toolchain and a second build step.

**Trigger for choosing this:** the doc tree outgrowing GitHub's rendering — cross-references between RFCs, or wanting search across them. Not true yet at 14 documents.

### Option C — full clone, Astro landing + MkDocs docs

Their stack as-is. Justified when there is a *marketing* story to tell that a catalogue can't: a named operating model, a multi-stage workflow diagram, a "how it works" narrative. agent-ready-repo has one (three supervised loops, gates G0–G5). skilldrop's equivalent pitch is closer to "49 skills, copy the folder" — which the catalogue *is*.

**Recommendation: A now, B when the doc tree justifies it, C only if skilldrop grows a model to explain.** A and B are additive — choosing A does not close the door on either.

## Proposal (assuming Option A)

- **`build_site.py`** (repo root, stdlib only, no network): manifests → `build/index.html`. Fails loudly on a skill missing from `packs.json` or `model-routing.json` rather than emitting a half-row.
- **`build/`** added to `.gitignore` — generated output is never committed, same discipline as `node_modules`.
- **Base path `/skilldrop/`**: every asset and internal link is relative. No absolute `/…` paths anywhere — this is the single most common project-pages breakage.
- **`.github/workflows/pages.yml`**: separate from `release.yml` so a site change can never touch the npm publish path. `permissions: pages: write, id-token: write`; builds on PR, deploys on `main` only.
- **No staleness check — it would be solving a problem this design doesn't have.** An earlier draft of this RFC proposed one in `validate.py`. That is incoherent alongside gitignoring `build/`: if the output is generated fresh in CI on every run, it cannot be stale, and in a clean clone there is nothing to compare against. The staleness check only makes sense if the built site is *committed*, which is the option this RFC rejects. What actually protects the site is upstream: `build_site.py` refuses to emit a page when a skill is missing from `packs.json` or `model-routing.json`, and `validate.py` already enforces description sync, tier sync, and pack membership on the manifests the generator reads. `--check` survives as a local convenience for diffing a build, not as a CI gate.
- **README** gains the site link; `skilldrop-cli-design.md:296`'s open question is answered and marked so.
- **No content on the site that isn't in the repo.** Every string is generated or is the page shell.

## Alternatives considered

- **A README table and nothing else (status quo):** rejected — cannot filter 49 skills across 229 tags, and cannot deep-link one skill.
- **Hand-written HTML catalogue:** rejected outright — a third unchecked copy of every description. This is the exact failure `validate.py` exists to prevent.
- **Astro for a single landing page (Option C's front half):** rejected for now — a framework whose value is components and routing, applied to one static page.
- **Publish the catalogue as JSON only, no HTML:** rejected as insufficient alone, but `build/catalogue.json` is worth emitting alongside the page: it is the registry index `skilldrop-cli-design.md` asks about, and third-party catalog authors could conform to it.
- **A `skilldrop.dev` domain:** deferred — a custom domain is a `CNAME` file away once the site exists and is worth having.

## Decision

{Pending review. Option A is recommended; B and C remain additive.}
