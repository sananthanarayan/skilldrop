---
rfc: 0067
title: A benchmark arm for a skill's scripts without its instructions
status: implemented
date: 2026-10-27
author: sanjay-ananth
---

# RFC-0067: A benchmark arm for a skill's scripts without its instructions

## Problem / use case

On Sonnet 5.5, the catalogue's skills meet more of the judges' checks than the plain agent, 83%
against 78%. But blind judges prefer the plain agent's answer: they picked the skill in only 40%
and 43% of pairs. On the held-out evals no revision or admission rested on, that falls to 32% and
35%. The roadmap's next step is to decide, per losing skill, whether to keep, rebuild rule-first
or retire it (RFC-0046).

The benchmark can't yet say why a skill loses. There are two arms, the whole skill and no skill.
A skill that ships a script could lose because its instructions are too heavy for a stronger
model, while the script still helps. Or it could lose because neither part adds anything. Those
two call for opposite decisions: rebuild it around the script, or retire it.

## Fit check

No skill changes. This is `run_bench.py`, which isn't part of the published package, plus its
docs. It's off by default, and runs only with `--backend claude-cli`, where an agent can run a
script.

## Proposal

**`--tools-arm` adds a third arm for each skill that ships scripts** (44 skills).
- **What it gets:** the skill's folder without its instructions: no `SKILL.md`, `reference.md`,
  `manifest.json`, `examples/` or `evals/`. Data a script reads, such as `templates/`, stays.
  Two scripts need it: `deck-builder` reads its palettes and `ai-usage-report` its report
  template.
- **Its system prompt is generated, never written:** the non-interactive line every arm gets,
  where the scripts are with each one's first docstring line, and "run one with --help". No
  rule from the skill reaches it, and a unit test checks that.
- **How it's judged:** against the eval's assertions, like the other arms. It's also judged in
  two more blind pairs per judge: the scripts only against the plain agent, and the skill
  against the scripts only. Each pair's A/B order is fixed by the eval, as before.
- **The cache:** its runs are keyed on a hash of what it was given, so changing a script reruns
  it. Changing only the instructions doesn't.

**The report adds a section per model.** It shows assertions met and cost for the three arms on
the same evals, and the three pairings for both judges. Each skill gets one of four readings:
*instructions help*, *the scripts carry it*, *the plain agent is preferred*, or *mixed*. Every
judge must agree, or it reads *mixed*. With a handful of evals per skill, a reading is a lead to
check against the outputs, not a verdict.

**What a decision rests on.** The keep, rebuild or retire list is chosen from the tier trials, as
the roadmap says. This arm is then run on those skills, and the reasons are read only after the
list is fixed. A rebuild is measured on fresh evals, as before.

## Cost

One more agent session per eval for a scripted skill, plus four more pairwise judgements with two
judges. For every scripted skill's 132 held-out evals, a trial is 396 agent sessions and 792
pairwise judgements.

**Pairwise judging is most of the bill.** Each pair reads both answers and the files the run
left behind. A one-eval smoke run cost $1.34, and $0.94 of that was the six pairs.

The estimate used to leave out the second judge's pairs and those input files. It now counts
both. It still runs low: it gave $0.67 for that $1.34 run, and $0.99 for an earlier two-arm run
that cost about $1.71. It puts a full trial at about $51 at list price, so budget up to about
$100 a trial.

**What the smoke run showed.** One trial of context-graph's eval 16, with both judges, ran all
three arms end to end. The scripts-only arm ran the script in four turns and found the planted
drift. Both judges preferred it to the full skill: it was shorter, as the request asked, and
made fewer claims it couldn't support. One eval is a check that the harness works, not a
finding.

## Alternatives considered

- **Hand-write a minimal SKILL.md per skill ("the one rule").** That's the rule-first rebuild
  itself, and it needs its own fresh evals. Measuring it on these evals would tune on them. The
  generated prompt can't carry a rule, so it measures the scripts alone.
- **Give the third arm the description too.** The description says what the skill is for, which
  is guidance. It's left out so the arm tests the scripts and nothing else.
- **Compare only the scripts with the plain agent.** Without the skill against the scripts, a
  skill whose instructions help on top of its scripts would read the same as one whose scripts
  do all the work.

## Decision

Accepted and implemented: `run_bench.py --tools-arm`, with unit tests in
`tests/test_run_bench_tools_arm.py`. Not yet run at scale. The first full run waits for the tier
trials, which fix the list of losing skills.
