---
rfc: 0070
title: A benchmark for loops against their own skills and the plain agent
status: implemented
date: 2026-11-03
author: sanjay-ananth
---

# RFC-0070: A benchmark for loops against their own skills and the plain agent

## Problem / use case

The benchmark measures skills (RFC-0040), and on current models the plain agent is preferred to
most of them (RFC-0067, RFC-0068). Loops have never been measured. The operating model rests on
the claim that a loop's order and gates add something its skills don't, and nothing tests that
claim. A loop could beat the plain agent only because its skills do, or lose to the plain
agent even though its skills win. A team deciding whether to adopt the loops has no number to go on.

## Fit check

No skill or loop changes. This is `run_bench.py`, which isn't part of the published package,
plus its docs. It's off by default, and runs only with `--backend claude-cli`, where an agent
can read the folders it's given.

## Proposal

**`--loops NAMES|all` benchmarks loops instead of skills.** It can't be combined with
`--skills` or `--tools-arm`. Each eval in a loop's `evals/evals.json` runs in three arms:

- **loop:** `LOOP.md` is the system prompt. The loop's folder and every stage skill's folder are
  in the working directory at `skills/<name>/`. A wrapper's `*` stage stages nothing.
- **stages:** the same stage skills, installed, with no loop. Its system prompt is generated
  from each skill's own `manifest.json` description, the way an agent sees installed skills.
  No rule from `LOOP.md` reaches it, and a unit test checks that.
- **baseline:** plain Claude Code, as for a skill.

Input files come from the loop's `evals/files/<eval id>/`, with the same `.fixture` and
`git-history.json` handling skills get. `--held-out` and `--evals` filter loop evals as they do
skill evals. A stage skill's pip requirements build the environment, as for a skill.

**How it's judged:** every arm against the eval's assertions. Then three blind pairs per judge:
the loop against the plain agent, the loop against its skills alone, and the skills alone
against the plain agent. Each pair's A/B order is fixed by the eval.

**The cache:** generation is keyed on a hash of the loop's folder and every stage skill's
folder, without their evals. Editing `LOOP.md` or a stage skill reruns the loop.

**The report** shows per model the three arms' assertions met and cost, the three pairings for
each judge, and a reading per loop. Every judge must agree, or it reads *mixed*:

| Reading | The blind pairs |
|---|---|
| the order helps | The loop beats its skills alone, and the plain agent |
| the skills carry it | The skills alone beat the plain agent, and the loop doesn't beat them |
| the plain agent is preferred | Neither the loop nor its skills alone beats the plain agent |
| mixed | Anything else |

## What the first measurement needs

The existing loop evals can't produce a result yet:

- **Their authors wrote them.** Each loop's author wrote its evals while writing the loop.
- **None is held out.** The report says so and calls a run on them a smoke test.
- **Some name files that don't exist.** `research` refers to a `sources/` folder, for example,
  and no loop eval has an `evals/files/` folder yet.

The first result needs at least two held-out evals per loop. Someone who has read only the
loop's description writes them, and each one comes with the input files it names. A loop that
reads *the skills carry it* or *the plain agent is preferred* on those evals goes to the same
keep, rebuild or retire question RFC-0046 asks of a skill.

## Cost

A loop eval is three agent sessions, three assertion gradings and three pairwise judgements per
judge. Loop sessions run longer than skill sessions, because each one reads several skills.
`--dry-run` prices a run before anything is spent.

## Alternatives considered

- **Two arms, loop against the plain agent.** It can't tell a loop that adds order from one
  that only carries its skills, which is the question the operating model turns on.
- **Benchmark the skills one by one and add the results up.** The loop's claim is about what
  happens between the skills. Per-skill results can't see a gate that sends work back.

## Decision

Implemented in 1.3.0: `run_bench.py --loops`. The first loop measurements are in RFC-0074.
