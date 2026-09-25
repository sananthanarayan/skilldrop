---
rfc: 0030
title: Discovery surface — llms.txt, site repositioning, tutorial, loop evals
status: accepted
date: 2026-09-25
author: sanjay-ananth
---

# RFC-0030: Discovery surface

## Problem / use case

Four phases of work made skilldrop an operating model. Nothing about how it *presents itself*
changed, so the repository now understates what it is — to humans and to machines alike.

1. **No `llms.txt`.** 423 tracked files and no machine-readable index. A model evaluating the
   repo has to crawl or guess, and the two documents that most concisely answer "what is this"
   — `ARCHITECTURE.md` and `contracts/` — are the ones it is least likely to find.
2. **The site sells the pre-loops product.** The hero read *"A prompt gets you a draft. A
   skill gets you a deliverable."* — a pitch for a **skill**, written before loops existed.
   Loops sat fifth in the nav, behind the 57-skill catalogue: the differentiator behind the
   commodity. `guides/` and `ARCHITECTURE.md`, both written in RFC-0029, appeared exactly once
   each in 166KB of rendered HTML.
3. **Diátaxis had a hole.** Five how-to guides, one reference, one explanation, and **zero
   tutorials** — no page that walks someone through the thing the project now leads with.
4. **Loops had no evals.** 48 of 57 skills ship acceptance checks; 0 of 5 loops did. The
   least-tested primitive was the one on the front page.

## Fit check

A structural change; the golden rules it touches:

- **No new primitive** — `llms.txt` is a generated index, and the tutorial is a guide under
  the RFC-0029 contract.
- **Zero runtime dependencies** — preserved. `build_llms.py` is stdlib-only, like every other
  generator here.
- **One declared producer per generated path** — `llms.txt` is generated from `packs.json`,
  `loops/*/loop.json`, `contracts/`, `guides/` frontmatter and `package.json`, and
  `validate.py` fails on drift. This is the rule RFC-0028 established, applied to a new output.

## Proposal

**`build_llms.py` → `llms.txt`.** Generated, never hand-written. A stale index is *worse* than
no index, because a model trusts it — and the repo already has a live demonstration of that
failure mode in its own GitHub About field, which still described the catalogue as it stood
before loops existed. Sections: Start here, Loops, Contracts, Guides, Packs, Outcomes,
Reviewers, the full catalogue (pointing at the generated `catalogue.json`), Optional.

**Site repositioning.** New hero — *"Your agent can draft anything. It should not get to
decide everything."* — which states the reversibility argument the four loops implement.
Loops move to second in the nav and second on the page, ahead of the catalogue. Outcomes get
a real section instead of existing only as filter chips. A new Docs section surfaces
`ARCHITECTURE.md`, `guides/`, and `llms.txt`.

**A tutorial.** `guides/tutorial/follow-a-change-through-the-loops.md` walks one realistic
change — API rate limiting — from a stakeholder complaint to a closed incident, through all
four loops. It is organised around **what each gate refuses**, because that is the part a
reader cannot infer from a stage diagram.

**Loop evals.** `loops/<name>/evals/{evals.json,eval_queries.json}` for all five: 10 eval
cases and 35 trigger queries. The shape is checked by `validate.py` — `loop_name` matches the
folder, every case has a prompt and assertions, and `eval_queries.json` carries both
`should_trigger` polarities, because the false rows are what draw the boundary against a
sibling loop.

**Repository metadata.** The About description and topics are refreshed to mention loops.

## Alternatives considered

- **Hand-write `llms.txt`**, as agent-ready-repo does. Rejected: the repo's own About field
  is a live example of a hand-maintained summary going stale, and an index a model trusts is
  the worst place to accept that risk.
- **Leave the hero alone and add a loops banner.** Rejected: the headline is the one line
  most visitors read, and it was advertising the previous version of the project.
- **Skip the tutorial; point at the loop README files.** Rejected: a `LOOP.md` explains one
  loop to someone who already bought the model. A tutorial is what sells the model, and
  Diátaxis names it as a distinct job for exactly that reason.
- **Skip loop evals** on the grounds that a loop is "just a sequence". Rejected: the sequence
  is the claim, so it is the thing most worth testing — and two of the ten cases encode
  failure modes (routing `REVISE` to the wrong stage, treating `PROCEED WITH CONDITIONS` as
  `PROCEED`) that a stage table cannot prevent.

## Decision

Accepted 2026-09-25. Implemented by the PR adding `build_llms.py`, `llms.txt`, the site
repositioning, `guides/tutorial/`, and `loops/*/evals/`.
