---
rfc: 0074
title: Every loop measured against its own skills, and four retired
status: implemented
date: 2026-11-05
author: sanjay-ananth
---

# RFC-0074: Every loop measured against its own skills, and four retired

## Problem / use case

A loop orders skills and puts a gate between them (RFC-0028). Until 1.4.0 no loop had been
measured, so nothing showed that the order and the gates add anything. RFC-0070 built the arm
that can show it, which runs each loop eval three ways: the loop, its stage skills installed
without it, and the plain agent. RFC-0046's question for a skill, "what rule does it add that
the plain agent breaks?", becomes, for a loop: **what do its order and gates add that its own
skills, used without it, don't do?**

## Evidence

Every loop ran on two held-out evals, written blind from its description: two trials on
`claude-sonnet-5-5`, with two blind judges.
- The four loops from 1.3.0: [`loops-1.3.0.json`](../benchmarks/loops-1.3.0.json).
- The 11 older loops: [`loops-1.4.0.json`](../benchmarks/loops-1.4.0.json), $53.36.

| Loops | Checks met: loop / skills / plain | Loop preferred to the plain agent (judges 1, 2) | Loop preferred to its skills |
|---|---|---|---|
| The four from 1.3.0 | 88% / 50% / 32% | 75%, 69% | 50%, 62% |
| The 11 older | 82% / 65% / 55% | 52%, 48% | 41%, 35% |

- **Clearly ahead of their own skills:** `ship-agent`, `release` and `modernize`.
- **Behind their own skills with both judges:** `adopt`, `apply`, `operate`, `discover` and
  `measure`. Each was read run by run, by one analyst per loop, as RFC-0068 did for skills.

| Loop | Against its skills (judges 1, 2, of 4) | What the outputs showed | What it adds that holds | Verdict |
|---|---|---|---|---|
| `adopt` | 0, 0 | Its rules narrowed the policy to the first use case when the team had no rules, and its gate swapped out the use case the sponsor had chosen | None | **Retire** |
| `apply` | 0, 0 | Its fit gate stopped before writing anything when the candidate had already decided to apply. Its confirm gate left form answers blank | None the skills don't already do | **Retire** |
| `operate` | 0, 0 | Same content as its skills, which already hand off to each other. It broke its own one rule in both incident runs | None | **Retire** |
| `discover` | 1, 1; and 0, 0 against the plain agent | Its ratification gate refused to record an approval the requester had given in writing | None. Without the gate, it is its skills | **Retire** |
| `measure` | 0, 1 | Spec before review, verification queries and owner questions all helped. It lost on a gate that refused to propose a definition the teams had handed over | Its order | **Rebuild**, then re-measure |

**What every loop gets wrong.** Of the judge reasons where a loop lost, the closing gate line,
gate ids and verdict words in the reply (`G4: BLOCKED`) were cited more than 30 times across
the five loops read. The run-log line ("`SKILLDROP_LOOP_LOG` isn't set") was cited 9 times. Every
`LOOP.md` asks for both. They explain some losses, but not the retirements above, each of
which also turned on a rule of its own.

## Proposal

- **Retire `adopt`, `apply`, `discover` and `operate`.** Each folder goes, and `catalogue.json`
  keeps a record with `"kind": "loop"` saying why and what to use instead.
  - `outdated`, `update`, `doctor`, `diff`, `install --loop` and `search` name an installed
    copy, with the reason, and remove nothing.
  - `validate.py` checks a retired loop's name only where it reads as the loop: "the `x`
    loop", `--loop x`, or `loops/x`. That's because `apply` is also a `provision` stage and a
    Terraform command.
- **The lifecycle keeps five stages.** Stages 1 (find the problem) and 5 (run it) have no
  loop. The operating-model picture draws them from their skills, in order and without a
  gate. G0 and G4 go with their loops, and the other ids keep their numbers.
- **`judge-audit` 0.4.0 is kept.** It was rebuilt on RFC-0072's rules and measured on two
  fresh blind evals with `--allow-bash`. Both judges preferred it in 3 of 4 pairs, and it met
  59% of checks against 44%. The reasons cite the rebuilt rules: per-run rows with the flipped
  items, and "can't tell" where an interval spans the user's bar.
- **Four skills move to heavy:** `bug-triage`, `prd-draft`, `prompt-caching-advisor` and
  `subagent-design`. RFC-0073 measured them heavier in both tier trials. Each now ships its
  `examples/` oracle.

**Next, not in this change:**
- Every remaining loop keeps gate ids, verdict words and the run log out of the reply, and
  writes the verdict to the run log alone.
- `measure` is rebuilt as above.
- All of them are re-measured on fresh blind evals.

## Alternatives considered

- **Fix the shared reply habit first, then decide.** The four retired loops each lost on a rule
  of their own as well: a gate that stopped, narrowed or overrode the user. Fixing the reply
  would leave each, at best, level with its own skills, which is still nothing added.
- **Keep the lifecycle loops for the story the picture tells.** The picture is meant to be
  true. A stage that does better with its skills alone says so.
- **Retire the loops outright, with no record.** An installed copy would then fail as an
  unreachable source, when it should say why it stopped updating, as a retired skill does.

## Decision

Implemented on branch `sanjay-ananth/loops-verdicts-and-baseline`.
