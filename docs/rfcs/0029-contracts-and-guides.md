---
rfc: 0029
title: Machine-readable contracts, guides, and an architecture doc
status: accepted
date: 2026-09-25
author: sanjay-ananth
---

# RFC-0029: Machine-readable contracts, guides, and an architecture doc

## Problem / use case

Three gaps, all the same shape — **the authoritative statement of something lived only in
prose**, so it could rot without any check noticing.

1. **The manifest shape existed only as a paragraph in AGENTS.md.** A contributor had to read
   and obey it. `validate.py` checked a flat list of required *field names* and nothing about
   their shape, so `"tier": "claude-opus-5"` — a direct violation of the golden rule that
   tiers are abstract — passed the lint. So did a non-semver version, a `deps` block missing
   `pip`, and an empty `tags`.
2. **The README had grown to 714 lines.** Roughly 200 of those were per-IDE install steps and
   script-invocation detail that a newcomer does not need in their first two minutes, and
   that a returning user cannot navigate to.
3. **There was no architecture document.** The system's shape was distributed across 28 RFCs
   and AGENTS.md's file-placement table. Nothing said, in one place, what the primitives are,
   what the install contract is, or which properties are load-bearing — which is exactly what
   someone evaluating the repo needs.

## Fit check

A structural change; which golden rules it touches:

- **Golden rule 2 (don't move `skills/`, `LICENSE`, `README.md`)** — honoured. README stays
  put and keeps everything `validate.py` requires of it (a row per skill, every pack name,
  every agent, every loop). Only long-form material moves.
- **Zero runtime dependencies** — preserved, and this is the design constraint that shaped
  the solution. The contracts are JSON Schema documents, but they are checked by a
  ~50-line stdlib subset validator in `validate.py`, not by `jsonschema`. If a contract ever
  needs a keyword the subset lacks, the answer is to teach the subset.
- **New top-level directories** — `guides/` and `ARCHITECTURE.md` are proposed here with
  rationale, as the rule requires.

## Proposal

**Contracts.** Four schemas join `loop.schema.json` and `terminals.json` in `contracts/`:
`skill.schema.json`, `pack.schema.json`, `agent.schema.json`, `guide.schema.json`. All closed
(`additionalProperties: false`), so a typo'd key fails rather than being ignored.
`validate.py` gains `check_schema()` — the subset of JSON Schema the contracts actually use
(`type`, `required`, `properties`, `additionalProperties`, `enum`, `const`, `pattern`,
`items`, `minItems`, `minimum`, `maximum`) — and runs every manifest, `packs.json`, every
`loop.json`, every agent frontmatter, and every guide frontmatter through it. The flat
`REQUIRED_FIELDS` list and the hand-rolled `_closed()` helper are deleted; the contract
subsumes both and catches shape errors neither could.

**Guides.** `guides/` holds the long-form material, split by Diátaxis **kind declared in
frontmatter, not by directory** — the directory is a convenience, the frontmatter is the
contract. That keeps the tree shallow while still forcing each page to declare which of the
four jobs it does. `validate.py` checks the frontmatter against `guide.schema.json` and
fails any guide not linked from `guides/README.md`, because an unindexed guide is unfindable.

**ARCHITECTURE.md.** One document: the four primitives, why a loop is not a long skill, why
the loops are separated by reversibility, the copy-never-transform install contract and its
single exception (agent projection), the enforcement table, and the five invariants worth
protecting.

## Alternatives considered

- **Add `jsonschema` as a dependency.** Rejected outright. Zero runtime dependencies is the
  property that makes an outside contributor's PR go green with no provisioning and makes
  `npx skilldrop-cli` immune to a transitive break. A 50-line checker is a much smaller cost
  than that property.
- **Directory-enforced Diátaxis** (`guides/<kind>/` being the contract). Rejected: it forces
  a deep tree for a small repo and makes a page's kind un-checkable when someone files it
  wrong. Frontmatter `kind` is checkable; a directory is not.
- **Leave the README long and add a table of contents.** Rejected: a TOC makes a long page
  navigable but still puts per-IDE install detail in front of a first-time reader.
- **Fold ARCHITECTURE.md into AGENTS.md.** Rejected: AGENTS.md answers *what do I do*, and is
  already long. Architecture answers *how is this built and why* for someone deciding whether
  to adopt it — a different reader with a different question.

## Decision

Accepted 2026-09-25. Implemented by the PR adding `contracts/{skill,pack,agent,guide}.schema.json`,
`check_schema()` in `validate.py`, `guides/`, and `ARCHITECTURE.md`.
