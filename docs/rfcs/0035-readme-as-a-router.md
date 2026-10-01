---
rfc: 0035
title: README as a router
status: implemented
date: 2026-10-01
author: sanjay-ananth
---

# RFC-0035: README as a router

## Problem / use case

The README had grown to 584 lines. It held all 63 skills in category tables, six generated
loop diagrams, the routing model, pack and outcome tables, both install routes in full, and
the reviewer-agent targets. Most of that is now the site's job: it has pack pages with a
starter prompt, a searchable catalogue, and a docs portal. Two copies of one inventory drift,
and the drift showed up three times in a single review (wrong plugin, persona and target
counts). A newcomer also had to scroll past six diagrams before reaching the first command.
agent-ready-repo's README is 65 lines and routes readers to its site; this RFC does the same.

## Fit check

Structural change: it changes what `validate.py` requires of the README and where
`build_loops.py` writes.

- **No content is lost.** The skill tables and skill anatomy move to
  `guides/reference/skill-catalogue.md`, the loop section and diagrams to
  `guides/reference/loops.md`, and the install sections to `guides/how-to/install.md`. The
  reviewer-agent detail was already in `agents/README.md`, and routing in `MODEL-ROUTING.md`.
- **Coverage checks move with the content.** `validate.py` still fails on a skill with no
  catalogue row, a loop missing from the loop reference, an agent missing from
  `agents/README.md`, and a pack the README's role list does not name. The headline skill
  count in the README is still checked.

## Proposal

The README is about 60 lines, in this order:

1. A one-paragraph pitch and a flow line.
2. Links to packs, catalogue, docs, install and contributing.
3. **Choose your role:** one line per pack, linking to its site page.
4. **Start in one command:** one install command, the pack's starter prompt, and what a good
   result looks like.
5. **How it works:** four bullets.
6. **Go deeper:** links.

`build_loops.py` writes the generated diagrams into `guides/reference/loops.md` instead of the
README. AGENTS.md, CONTRIBUTING.md, the authoring guide and `contribution-wizard` now say to
add a new skill's row to the skill catalogue guide. Only a new pack needs a README line.

## Alternatives considered

- **Keep the long README and fix the drift.** Rejected: the drift is structural, because one
  inventory lives in two places. Fixing the counts once leaves the cause in place.
- **Generate the README from data.** Rejected: a generated README reads like a generated
  README. The parts that need generating already have a producer (the site, and the loop
  diagrams).

## Decision

Accepted 2026-10-01 and implemented in the same PR as the site's pack-discovery work.
