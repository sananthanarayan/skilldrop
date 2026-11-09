---
rfc: 0081
title: A manuscript check for research
status: implemented
date: 2026-11-09
author: sananthanarayan
---

# RFC-0081: A manuscript check for research

## Problem / use case

Revising a paper, thesis chapter or report leaves faults that reviewers and examiners notice:
"Kuh et al., 2009" in the text after the list says 2008, a name misspelt in the list, a reference
listed twice, numbered references out of citation order, "see Figure 3" after a figure was cut,
and an abstract figure that no longer matches its table. A capable agent reads a manuscript
fluently and misses the mechanical ones, because it reads what the author meant. `research`
plans questions and synthesises sources; nothing checks the researcher's own manuscript before
it goes out.

## Fit check

- **Concrete artifact:** a fix list of citation, cross-reference and consistency faults with
  lines, and the full renumbering when numbered references are out of order.
- **Portable:** a plain folder; a stdlib Python 3.9+ script that reads only the file it is given,
  writes nothing, and contacts no network.
- **Opinionated:** the script decides pass or fail; the skill leads with what a reviewer would
  catch, names the likelier side of each mismatch, deletes nothing unasked, and checks the
  manuscript's own numbers and claims for consistency.
- **Category:** joins `research` and its outcome, because its users are researchers.

## Proposal

| Skill | Tier | Script |
|---|---|---|
| `manuscript-check` | standard | `manuscript_check.py`: .md, .txt and .docx; numbered and author-year citations both ways with near misses (wrong year, misspelt name, missing year letter); duplicates by DOI or title (Vancouver and IEEE titles too); Figure, Table and Section references and captions; footnotes; DOIs; abstract length; the old-to-new renumbering for citation order |

## Alternatives considered

- **A separate `editor` pack.** Its users are researchers, who already browse `research`; a pack
  with one skill for the same people splits them.

## Measurement

Two held-out evals each round, written blind; two trials on `claude-sonnet-5-5`; judges
`claude-sonnet-5-5` and `claude-opus-5-5`; `--allow-bash`.

| Draft | Pairs won (judges 1, 2, of 4) | Checks met: skill / plain |
|---|---|---|
| 1 | 0, 0 | 89% / 93% |
| 2 | 2, 2 | 82% / 68% |

- **Draft 1** found every reference fault the plain agent found, and lost on what else a reviewer
  checks: a total in the text that didn't match its table, an abstract claim the results didn't
  show, a full renumbering plan, and exact line numbers.
- **Draft 2** checks the manuscript's own numbers and claims against its tables and results,
  gives the whole renumbering from the script's old-to-new map, and quotes the script's line
  numbers. It won the author-year paper in all four judgements, finding that an abstract's 23%
  came from dividing by the wrong value, and is admitted at the bar.

## Decision

Implemented in 1.12.0: `manuscript-check` in `research`.
