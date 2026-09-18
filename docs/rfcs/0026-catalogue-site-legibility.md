---
rfc: 0026
title: Catalogue site legibility
status: implemented   # draft → accepted | rejected → implemented
date: 2026-09-18
author: sananthanarayan
---

# RFC-0026: Catalogue site legibility

## Problem / use case

The catalogue site (RFC-0011) hides its best feature. The search box, both filter chip rows,
and all 56 skill rows live inside `<details class="more" id="all">`, so a first-time visitor
sees the words "See all 56 skills" and nothing else until they click. Three further gaps show
up against any comparable catalogue site:

- **Filter state is unshareable.** `active = {pack, tier}` lives only in JS memory; the URL
  never changes. "Here's the product-manager pack" is not a link anyone can send.
- **Nothing on the page dates the project.** No version, no release, no changelog. A stranger
  cannot tell whether skilldrop shipped last week or was abandoned in 2025.
- **The only browse axis is role.** Packs answer *who needs this*. A visitor who does not
  self-identify as `solution-architect` has nothing to click. The README's nine categories
  answer *what kind of thing is this*, but they exist only as prose headings — no machine-
  readable form, so the site cannot offer them.

## Fit check

This is a structural change, not a skill. Golden rules touched:

- **Rule 2 (do not move `skills/`, `LICENSE`, `README.md`)** — untouched; nothing moves.
- **Rule 4 (never invent commands or file conventions)** — one new top-level file, `CHANGELOG.md`,
  and one new key in `packs.json`. Both are documented in AGENTS.md **File placement** in the same
  change, and both are enforced by `validate.py` so neither can drift into fiction.
- **RFC-0011's single-source rule** — every new fact on the page is read from a file that already
  exists or from the two new sources above. No fourth copy of a string is typed into `build_site.py`.

## Proposal

Five changes, all inside `build_site.py` except where noted.

1. **Open the catalogue.** `<details>` becomes a plain section: heading, controls, and grid are
   always in the DOM and always visible. To keep RFC-0011's "do not dump 56 paragraphs at a reader
   who has not chosen yet" intent, JS hides rows past the first 12 behind a `Show all N` button,
   and auto-expands the moment a query, a filter, or a hash deep-link is active. Without JS every
   row renders — the disclosure is progressive enhancement, never a gate.
2. **Put filter state in the URL.** `?q=&pack=&tier=&outcome=` written with `history.replaceState`
   on every change and read back on load. A filtered view becomes a link without adding a page.
3. **Outcomes as a browse axis.** A new `outcomes` key in [`packs.json`](../../packs.json) —
   the README's nine categories restated as six outcomes, each `{description, skills[]}` —
   rendered as a third chip row. This is the existing taxonomy made machine-readable, not a
   fourth one invented. `validate.py` gains the same two-way check packs already get: every
   listed skill is a real folder, and every skill belongs to at least one outcome. Outcomes are
   a browse aid only; they are deliberately *not* an install unit, so the CLI is unchanged.
4. **Date the project.** A hand-maintained root `CHANGELOG.md` (`## <version> — <YYYY-MM-DD>`
   plus bullets) parsed by `build_site.py` into a "Recently shipped" section showing the three
   most recent releases, each linking to its npm version. The current version renders in the
   footer. `build_site.py` fails the build if `CHANGELOG.md`'s newest version disagrees with
   `package.json` — the same refuse-to-build-a-half-row discipline `collect()` already applies.
5. **A real footer.** Three columns — Project, Docs, Release — replacing the two bare links.

## Alternatives considered

- **Adopt a multi-page site** (per-pack pages, on-site docs, a separate changelog page), which is
  what the comparable site does. Lost: it needs a static-site generator and a docs pipeline, and
  RFC-0011's whole premise is one self-contained file with no external requests. The pitch is
  "copy a folder"; it fits on one page.
- **Generate the changelog from git tags.** Lost: CI checks out at depth 1 with no tags, and
  `build_site.py` shelling out to `git` would end its no-network, stdlib-only guarantee.
- **Ship outcomes as a third top-level JSON file.** Lost: `packs.json` is already the "who needs
  this" file and is already loaded by everything that would need outcomes. A second file is a
  second thing to keep in sync.
- **Do nothing.** Lost: item 1 alone means most visitors never see that the search exists.

## Decision

Accepted 2026-09-18 and implemented in the same change: `build_site.py`, `packs.json`,
`validate.py`, `CHANGELOG.md`, AGENTS.md file-placement table.
