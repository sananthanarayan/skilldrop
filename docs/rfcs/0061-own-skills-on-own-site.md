---
rfc: 0061
title: The catalogue's own skills on its own site and pull requests
status: implemented
date: 2026-10-21
author: sanjay-ananth
---

# RFC-0061: The catalogue's own skills on its own site and pull requests

## Problem / use case

skilldrop says its skills beat the plain agent, but it had never used them on itself in
public. A reviewer weighing the catalogue can fairly ask: if `accessibility-audit` and
`web-performance-review` are good, what do they say about skilldrop's own site?

## Fit check

No skill changes. The site's builders change where the review found problems. One reporting
workflow is added, and one explanation page.

## Proposal

**Run `web-performance-review` on the live site.**
- Lighthouse 13.5.0: three runs on the home page, and one each on the start, packs, catalogue,
  skill and docs pages, read through the skill's `lh_summary.py`.
- There's no field data yet, so it's lab only, and the page says so.
- **Fix applied:** the Prism theme stylesheet from jsDelivr blocked the docs pages' first paint,
  and was 84% of their LCP. It now loads without blocking, with a `<noscript>` copy.

**Run `accessibility-audit` (WCAG 2.2 AA)** on the built HTML and CSS, alongside Lighthouse's
automated checks. Three findings, all fixed:
- **2.4.7 Focus Visible:** on the home page's install tabs, only the last tab showed keyboard
  focus. Each radio now outlines its own label.
- **1.4.3 Contrast:** dark text on the accent was 4.47:1. It's now light text on the darker
  accent: 7.40:1 light, 8.57:1 dark.
- **1.4.11 Non-text Contrast:** search-field borders were 1.27:1. A new `--field-border`
  colour gives 3.71:1 light and 3.80:1 dark.

**Publish both reviews** in each skill's own output format, on
`guides/explanation/own-skills-on-own-site.md`, linked from the "How skills are checked" page.

**`.github/workflows/skill-review.yml`** runs `pre-merge-review`, through the repo's own action,
on each pull request.
- It reports to the job summary and never blocks.
- It runs only when `ANTHROPIC_API_KEY` exists, so never on forks or Dependabot pull requests.
- Output is capped at 6,000 tokens.
- `uses: ./` runs the action from the pull request's own branch. That's acceptable only
  because the secret reaches same-repo branches alone, whose authors already have write access.

## Alternatives considered

- **Make the skill review a required check.** A model's verdict is a second opinion. The merge
  decision stays with the required checks and a person.
- **Only fix the scanner's finding.** The two worst findings were ones a scanner can't make:
  keyboard focus, and field-border contrast. Fixing just the automated one would have
  demonstrated the opposite of the skill's point.

## Decision

Accepted and implemented in 0.16.42. Re-measured live after the deploy, with three runs each
side on the same settings: the docs page's median LCP went from 1.86 s to 0.98 s. A
screen-reader pass is listed on the page as still to do.
