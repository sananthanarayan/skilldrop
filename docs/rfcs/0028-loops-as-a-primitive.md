---
rfc: 0028
title: Loops as a primitive
status: accepted
date: 2026-09-25
author: sananthanarayan
---

# RFC-0028: Loops as a primitive

## Problem / use case

skilldrop is 57 skills, 6 packs, 7 outcomes and 3 subagents — a catalogue of parts. A
newcomer's first problem is not "is there a skill for this", it is "what order do I do these
in, and what stops me shipping something bad". The repo already answers that, but only as
prose nothing enforces:

- [`README.md`](../../README.md) opens with *"skilldrop runs two value streams, and nothing
  comes out of either until it passes a review gate"*, drawn in
  `docs/knowledge-work-pipeline.mmd` and `docs/code-implement-verify.mmd` — both since
  retired, their content now generated into [`docs/loops/`](../loops/) from `loop.json`.
- [`agent-loop-design`](../../skills/agent-loop-design/SKILL.md) already specifies the loop
  schema — "every loop has exactly these three state types" (generate / verify / gate), with a
  revision cap defaulting to 3.
- [`feature-implement-loop`](../../skills/feature-implement-loop/SKILL.md) is a working
  instance of that schema; [`pre-merge-review`](../../skills/pre-merge-review/SKILL.md) ships
  a real deterministic gate script.
- `packs.json` `outcomes` already reads as a lifecycle: decide → design → build → run.

So the sequences exist and are load-bearing, but they are not machine-readable, not
installable, not validated, and drift freely — the two `.mmd` files are hand-maintained twins
of the README's Mermaid blocks, with no producer relationship between them.

Meanwhile every gating skill invented its own terminal vocabulary for the same five outcomes:
`VERIFIED`/`BLOCKED`, `READY`/`NOT READY`, `PROCEED`/`REVISE`/`SPLIT`, `SHIP IT`/`MAJOR REWRITE`.

## Fit check

This is a structural change, so per the template: which golden rules it touches, and why it
doesn't break them.

- **Golden rule 1 (name triple-match)** — extended, not broken. A loop is held to the same
  triple: folder name = `loop.json` `name` = `LOOP.md` frontmatter `name`.
- **Golden rule 2 (don't move `skills/`)** — untouched. `loops/` is additive; no skill moves,
  and every one of the 57 stays installable exactly as before.
- **`CLAUDE.md`'s no-chaining rule** — *amended, deliberately*. The rule said skills compose
  only at the human's invocation layer. It now says sequencing is owned by a loop: a loop
  orders skills, and a skill still never invokes a skill. The portability property the rule
  protected is preserved in full — that is the point of putting sequencing in a new primitive
  rather than relaxing the ban.
- **Zero runtime dependencies** — preserved. `contracts/loop.schema.json` documents the shape
  for external tooling, but `validate.py` checks it with hand-rolled stdlib code. No
  `jsonschema` dependency.

## Proposal

Add `loops/<name>/` as the third primitive, beside `skills/` and `agents/`:

```
loops/<loop-name>/
├── LOOP.md      # what an agent reads: stages, how to run them, quality bar, anti-patterns
└── loop.json    # the machine-readable contract — stages, skills, gates, cap
```

A loop declares ordered `stages`; each stage has a `type` (`generate` / `verify` / `gate` —
the three `agent-loop-design` mandates), the `skills` it runs, and optionally a `gate`. A gate
has a repo-unique id (`G2`, `G2.1`), a `kind` (`mechanical` / `review` / `human`), the
`verdicts` it can emit, and the stage a revise-class verdict returns to. `cap` bounds revision
rounds; default 3.

Two new contracts:

- `contracts/loop.schema.json` — the closed loop shape.
- `contracts/terminals.json` — one verdict vocabulary in five classes (`pass`, `conditional`,
  `revise`, `redirect`, `blocked`), each verdict recording the skill it came from. A gate may
  not invent a new word for an existing outcome.

Two loops ship in this RFC, both **promotions of the diagrams that already exist** rather than
new inventions: `build` (from `code-implement-verify.mmd`) and `ship-a-draft` (from
`knowledge-work-pipeline.mmd`, as `kind: wrapper` — its middle stage is any generator).

`validate.py` gains a loops pass enforcing: the name triple, the closed schema, stage-id
uniqueness, every named skill resolving to a real folder, `*` only in a wrapper, repo-unique
gate ids, a mechanical gate's script existing, every verdict being in `terminals.json`, every
gate having both a pass and a non-pass verdict, every gate being able to emit `BLOCKED`,
`revise_to` pointing at an earlier stage, `Quality bar` + `Anti-patterns` sections, and
description sync. Loops are also excluded from `model-routing.json` with a named error —
a loop sequences skills and makes no model call of its own, so it carries no tier.

## Alternatives considered

- **Relax the no-chaining rule and let skills call skills.** Fewer concepts, closer to a
  conventional agent framework. Rejected: a chained skill stops working when installed alone,
  which destroys the copy-never-transform portability that is skilldrop's main advantage over
  heavier platforms. It also needs recursion guards the repo has no way to enforce.
- **Extend `packs.json` so a pack can declare an ordered sequence.** Smallest diff, no new
  directory. Rejected: packs answer *who needs this* and outcomes answer *why*; adding *in
  what order* overloads a structure whose two existing axes were deliberately kept separate.
- **Do nothing; keep the pipelines as README prose.** Rejected: the prose already drifts — two
  `.mmd` files duplicate the README blocks with no producer relationship, and no check would
  notice if a renamed skill broke a documented sequence.
- **Adopt agent-ready-repo's three loops verbatim** (discovery → build → release). Rejected on
  its own stated criterion — loops are separated by reversibility, decision authority and
  failure mode. skilldrop's `design` stage is 15 skills and does not fold into discovery, and
  the SRE skills have no home in a three-loop model.

## Decision

Accepted 2026-09-25. Loops ship as the third primitive with `build` and `ship-a-draft`;
`discover`, `design` and `operate` follow in the next release along with directional
hand-offs. Implemented by the PR that adds `loops/`, `contracts/`, and the `validate.py`
loops pass.
