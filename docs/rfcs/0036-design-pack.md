---
rfc: 0036
title: Design pack, brand-kit and marketing-flyer
status: implemented
date: 2026-10-01
author: sanjay-ananth
---

# RFC-0036: Design pack, brand-kit and marketing-flyer

## Problem / use case

The maintainer asked for a design pack holding the slide deck skill, a marketing flyer skill and
anything else visual, where the generators ask for the user's branding before they generate.
Today `deck-builder` lives in `stakeholder-comms` and can take a corporate template or a colour
palette. But without a template it never asks for a logo or fonts, and every deck repeats the
same brand questions. There is no flyer skill, so a team that needs an event flyer or a
one-page product sheet gets a generic layout in generic colours.

## Fit check

New pack, two new skills, and two skills moving between packs (RFC-0034 requires an RFC for
the move).

- **`brand-kit`.** *Artifact:* a `brand.json` (logo files, colour roles, fonts, voice,
  imagery, templates, contact and legal footer) plus a one-page `BRAND.md`. *Portable:*
  markdown and JSON, with a stdlib checker script. *Opinionated:* every colour needs a hex
  code; text-on-background contrast must be at least 4.5:1; a logo PowerPoint can't read (SVG,
  EPS) is flagged for PNG export; every value says where it came from.
- **`marketing-flyer`.** *Artifact:* a self-contained, print-ready HTML flyer (Letter, A4,
  A5 or a square social size), which saves to PDF from any browser, or through headless Chrome
  with `--pdf`. *Portable:* a stdlib script, with images embedded so the one file is the whole
  flyer. *Opinionated:* one call to action, a headline of ten words or fewer, the user's own
  facts only (dates, prices, contact), and checked contrast.
- **Rule 7 (a skill never invokes a skill).** `deck-builder` and `marketing-flyer` each
  *read* a `brand.json` if one exists, and otherwise ask the brand questions themselves. Each
  still runs alone; `brand-kit` only saves the user from answering twice.

## Proposal

- **`packs/design/`** holds `brand-kit`, `deck-builder`, `marketing-flyer` and
  `slide-outliner`, and requires `core`. `deck-builder` and `slide-outliner` move from
  `stakeholder-comms`, which keeps `audience-profile`, `exec-summary`, `decision-log` and
  `guide-builder`. `slide-outliner` moves with `deck-builder` because the outline feeds the
  build.
- **`deck-builder` 0.3.0.** The setup block asks for branding first: a `brand.json`, or a
  template, logo files, colours and fonts. `build_deck.py --brand brand.json` (or a `brand`
  field in the spec) fills in whatever the spec leaves out. On the built-in design, the logo
  goes on every slide (using the on-dark version on dark slides) and the brand's heading and
  body fonts are applied. A template still wins for chrome.
- **New outcome:** `create-on-brand-collateral`, for marketers, designers and anyone making a
  deck or flyer.
- **Model tiers:** both new skills are `standard`.

## Alternatives considered

- **Brand questions only inside each generator, with no `brand-kit`.** Rejected: every deck
  and every flyer asks the same eight questions, and the answers drift between them.
- **A PDF library for the flyer** (reportlab, weasyprint). Rejected: it breaks the
  zero-dependency default for a skill that needs none. HTML with print CSS prints exactly in
  every browser, and headless Chrome turns it into a PDF when it is installed.
- **Keep `deck-builder` in `stakeholder-comms`.** Rejected: the user asked for one home for
  visual work, and a deck is the design pack's main artifact.

## Decision

Accepted 2026-10-01 at the maintainer's request, and implemented in the same PR.
