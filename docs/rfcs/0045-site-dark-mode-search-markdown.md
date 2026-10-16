---
rfc: 0045
title: Dark mode, full-text search and fuller markdown on the Python-built site
status: implemented
date: 2026-10-16
author: sananthanarayan
---

# RFC-0045: Dark mode, full-text search and fuller markdown on the Python-built site

## Problem / use case

Comparing the docs with agent-ready-repo's Astro/Starlight site showed four things skilldrop's
site lacked: a dark theme, search over the full text of every page (the dialog searched names,
summaries and a short slice of each body), markdown that renders nested lists, task lists and
quoted documents, and plain-text meta descriptions (skill descriptions leaked `**bold**` into
link previews). Moving to Starlight would bring all four, at the cost of 271 npm packages, a
migration, and a second language in the site build.

## Fit check

A structural change to the site, not to a skill. It keeps the invariant that matters: the
published package and the repo's own tooling stay dependency-free. One build-time tool joins the
Pages workflow, outside `package.json` and outside the published package.

## Proposal

- **Dark theme.** Every page already defines the same colour variables; the nav, search and
  footer now read them too. `THEME_CSS` in `build_site.py` redefines them on `<html>` when the
  system prefers dark or the reader picks dark with the nav toggle (remembered in
  `localStorage`). `build_loops.py` draws `docs/loops/operating-model-dark.svg` beside the light
  picture, and a guide image marked `#gh-dark-mode-only` / `#gh-light-mode-only` shows in the
  matching theme, on GitHub and on the site alike.
- **Full-text search.** `pages.yml` runs Pagefind, pinned (`npx --yes pagefind@1.5.2 --site
  build`), after the Python build. Each indexable page marks its content `data-pagefind-body`
  with a `kind`. The search dialog keeps its instant name and summary matches from
  `search.json` and adds Pagefind's full-text matches below them; a local build without the
  Pagefind step still searches.
- **Fuller markdown.** `render_md` renders nested and ordered lists (with a start number),
  `[ ]` / `[x]` task items, `_emphasis_`, `~~strikethrough~~`, `<https://…>` autolinks, and
  blockquotes that hold their own headings, lists and paragraphs.
- **Plain meta descriptions.** `head_meta` strips markdown marks before writing a description.

## Alternatives considered

- **Move the site to Astro/Starlight now.** Brings in-page components as well, but adds a Node
  dependency tree to upkeep and either two site stacks or a port of the Python generators.
  Kept open: the generators could later write markdown and JSON for Starlight to render, and
  this RFC's choices (variables for colour, `data-pagefind-*` markers, standard markdown) carry
  over to that move rather than block it.
- **A hand-built full-text index in `search.json`.** Shipping every page's full text to every
  visitor on first search grows with the docs; Pagefind loads only the index fragments a query
  needs.

## Decision

Accepted and implemented in 0.16.12.
