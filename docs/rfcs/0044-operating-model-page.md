---
rfc: 0044
title: Operating model page, gate codes in lifecycle order, and a page standard for guides
status: implemented
date: 2026-10-16
author: sananthanarayan
---

# RFC-0044: Operating model page, gate codes in lifecycle order, and a page standard for guides

## Problem / use case

skilldrop calls itself an operating model, but no page shows the model. A newcomer who wants
to know which stage their work is in, which pack helps there and where the agent will stop
has to piece it together from `ARCHITECTURE.md` (not on the site), the two loop guides, the
README and `contracts/terminals.json`. There are seven per-loop diagrams and none of the whole.

Three smaller problems came up while comparing the docs with agent-ready-repo's
operating-model page:

1. **Gate codes do not follow the work.** `release` was added between `build` and `operate`
   as G2.5 and G2.6, so `operate` is G3, `ship-a-draft` G4 and `apply` G5 and G6. A reader
   cannot tell from a code where the work is.
2. **The docs are arranged only by Diátaxis kind.** The stages a user thinks in appear
   nowhere in the sidebar.
3. **Guides drift.** Counts that nothing checks had gone stale (`57 skills`, `8 packs`,
   `all 63 skills`, "four lifecycle loops" in a tutorial that skipped `release`), four how-to
   pages opened with a heading, and tutorials used "Step N" headings.

## Fit check

A structural change, not a skill. It touches golden rule 7 (a loop orders skills) only by
renaming gate ids, which are repo-unique strings in `loop.json`; no skill gains a dependency
on another. It adds no runtime dependency: the picture is stdlib Python writing SVG text.

## Proposal

- **An operating-model guide**, `guides/explanation/operating-model.md`: the five stages in a
  table, a short section per stage, where the agent waits for you, the shared verdicts, how
  to read a gate code, the two loops outside the lifecycle, and the install command.
- **A generated picture**, `docs/loops/operating-model.svg`, written by `build_loops.py` from
  every `loop.json` and the pack folders. Only the plain-English lines per loop live in the
  generator (`LIFECYCLE`, `OUTSIDE`); a loop without them fails `--check`, so a new loop
  cannot be left out of the picture. `build_docs.py` renders an image on a line of its own
  and publishes the SVG beside the pages.
- **Gate codes in lifecycle order.** The whole number is the loop's place, G0 at `discover`
  through G4 at `operate`; a decimal is a second gate in the same loop. The loops outside the
  lifecycle take the next numbers. Renames: G2.5 → G3, G2.6 → G3.1, G3 → G4, G4 → G5,
  G5 → G6, G6 → G6.1. RFCs and changelog entries keep the codes they were written with.
- **A stage-grouped docs sidebar.** Guide frontmatter gains an optional `stage`; generated
  pack guides take their pack's earliest lifecycle loop. The sidebar is Start here, then one
  group per stage (the loop's page first), then the rest by kind, each page once.
- **A page standard for guides** in AGENTS.md § Writing a guide, with `validate.py` enforcing
  what a script can see: the title is the H1, no "Step N" headings, no filler words in prose,
  and a how-to opens with a sentence.

## Alternatives considered

- **Put the picture in Mermaid**, like the per-loop diagrams. Mermaid lays out a five-stage
  flow with nested gates poorly, needs a CDN script on the page, and does not render in an
  `<img>`. Rejected.
- **Hand-draw the SVG**, as agent-ready-repo's generator hard-codes its stage data. It would
  drift from `loop.json` the first time a loop changed. Rejected.
- **Keep the gate codes** and explain the gaps. Every page that names a gate would need the
  explanation. Rejected; the rename touches six ids once.
- **Move the docs to Astro/Starlight** for the stage navigation. Adds a Node build and a
  dependency tree to a repo whose tooling has none. Not taken here.

## Decision

Accepted and implemented in 0.16.10.
