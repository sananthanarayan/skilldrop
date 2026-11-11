---
rfc: 0083
title: Loop replies in plain words, and the measure loop rebuilt
status: implemented
date: 2026-11-12
author: sanjay-ananth
---

# RFC-0083: Loop replies in plain words, and the measure loop rebuilt

## Problem / use case

RFC-0074 measured every loop against its own skills, used without it. The judges' commonest
reason for preferring the skills was the reply itself, cited in more than 30 of the reasons the
losing loops lost on:
- the closing gate line (`G4: BLOCKED`);
- verdict words, and stage and skill names;
- talk of the run log ("`SKILLDROP_LOOP_LOG` isn't set").

Four loops told the agent outright to close with their gate lines. The rest drifted into gate
talk, because each `LOOP.md` is written in it. The four loops retired by RFC-0074 also lost when
a person's decision held back work that could have been delivered, or when the loop refused to
record a decision the request already contained. `measure` lost the same way, but its order
helped, so RFC-0074 named it for a rebuild.

## Fit check

A change to all eleven `LOOP.md` files and to the loop contract's required sections. No
skill, gate id, verdict vocabulary or `loop.json` shape changes. The verdicts still exist; they
are recorded in the run log and kept out of the reply.

## Proposal

**Every `LOOP.md` gains `## What the reply says`,** after `## How to run this loop`.
`validate.py` requires it. It says:
- **Lead with what the person asked for, in plain words.**
- **No loop internals:** no gate id, verdict word, stage or skill name, or skill-folder path in
  the reply or in any file the person receives. The outcome is said in plain words instead.
- **The verdict goes to the run log only,** and the reply never mentions the run log.
- **A person's decision never holds back the work.** Everything up to it is delivered, then the
  decision is named in one line. A decision the request already contains is recorded as theirs.
- **Stop only when nothing can be made,** saying in plain words what is missing.

The instructions that contradicted it are removed, among them four loops' "close with each gate
on its own line" and research's exception for its own verdict.

**`measure` 0.2.0, as RFC-0074 named:**
- **A handed-over definition.** When the people asked hand the definition to the analyst, it
  proposes one, marked unconfirmed, and carries on.
- **What can be built now ships,** and it says plainly who confirms what.
- **No unasked spec.** When only the numbers were asked for, there's no spec document.

## Measurement

All 11 loops ran on two fresh held-out evals each, written blind from their descriptions: two
trials on `claude-sonnet-5-5`, judges `claude-sonnet-5-5` and `claude-opus-5-5`, with
`--allow-bash` ([`loops-1.14.0.json`](../benchmarks/loops-1.14.0.json), $40.12).

| | Before (RFC-0074, the 11 older loops) | After |
|---|---|---|
| Loop replies with a gate id, verdict word or run-log talk | 38 of 44 | 0 of 44 |
| Loop preferred to the plain agent (judges 1, 2) | 52%, 48% | 65%, 70% |
| Loop preferred to its own skills | 41%, 35% | 52%, 59% |
| Checks met: loop / skills / plain | 82% / 65% / 55% | 85% / 77% / 74% |

The sets differ slightly: four loops were retired between the rounds and four added before the
first.

- **The rule held everywhere,** and the loops went from behind their own skills to even with
  them.
- **`measure` 0.2.0 moved from 0 and 1 of 4 pairs to 2 and 2 against its skills.**
- **Clearly ahead of their skills:** `ship-agent` (4 and 4 of 4), `clarify` (3 and 3) and
  `provision` (3 and 3).
- **Even or split:** `research`, `modernize`, `ship-a-draft`, `comply`, `measure` and
  `release`. `release` won every pair in the last round, so with two evals a loop's row swings.
- **Behind their skills with both judges:** `build` (0 and 1 of 4) and `design` (1 and 1). An
  analyst read every output. Neither leaked a gate id. They lost on what the loop pushed the
  agent to do:
  - **build:** it edited someone else's change when it should have reported a failed check,
    and missed a data-loss edge case its skills caught.
  - **design:** it wrote conditions into an ADR that the decider never set, and named files it
    hadn't written.
  - **both:** they described a review panel the agent had seated itself ("I didn't run the
    separate panel").

  `design` also showed a gain in one eval: threats and go-live conditions the other arms
  missed.

## Alternatives considered

- **Strip the verdicts from the loops.** The run log and `skilldrop loop-stats` read them, and a
  gate that decides needs a word to decide with. Keeping them out of the reply is enough.
- **Fix only the four loops that asked for gate lines.** The others leaked the same jargon
  without being asked, so the rule has to be in every loop.

## Decision

Implemented in 1.14.0: the section in every loop, and `measure` 0.2.0. `build` and `design` are
kept, to be rebuilt and measured a third time. Each rebuild covers:
- reporting a failed check on someone else's change, with the fix offered and not applied;
- recording only what a decider said;
- naming only files that exist;
- showing a review's evidence, or not mentioning the review at all.

A loop that loses a third time is retired, and its skills are run in order instead.
