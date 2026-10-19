---
title: Benchmark skills against the agent without them
summary: Run each acceptance eval twice as an agent session, with the skill and without it, and read the lift, the blind preference from two judges, and the cost.
kind: how-to
---

# Benchmark skills against the agent without them

You can measure whether a skill makes the agent's result better, and what that costs, by
running each of its evals with the skill and without it.

`run_bench.py` benchmarks the catalogue in the clone it sits in, so a skill of your own goes in
`packs/<pack>/skills/<name>/` with its `evals/evals.json`. You need Python 3.9 or newer and a
signed-in Claude Code; each run is a `claude -p` session on your plan, with no API key. Flags,
isolation and every number in the report are on [Benchmark options and report](../reference/benchmark-options.md).

## Price the run first

Ask for a dry run of the skills you want to measure.

```bash
python3 run_bench.py --backend claude-cli --skills adr-generator,md-to-xlsx --dry-run
```

It prints how many agent sessions and judgements the run needs and a rough cost at list price,
and spends nothing.

## Run the benchmark

Run each eval twice, with a second blind judge, under a $5 cap.

```bash
python3 run_bench.py --backend claude-cli --skills adr-generator --trials 2 \
  --second-judge claude-opus-5-5 --budget 5
```

Each arm runs in an empty, sandboxed directory with no network, and the results land in
`bench-results/`.

## Run a long benchmark from a terminal

A full catalogue run takes hours. Start it from your own terminal, detached, so an editor's or
an agent's task time limit can't stop it halfway, and follow the log:

```bash
nohup python3 run_bench.py --backend claude-cli --held-out --second-judge claude-opus-5-5 \
  --budget 60 > bench.log 2>&1 &
tail -f bench.log
```

If it stops anyway, run the same command again: every finished call is cached, so only what is
missing is paid for.

## Read the report

Open the report and compare both arms against the floor, the score a non-answer gets.

```bash
less bench-results/report.md
```

The blind preference says whether the skill makes the result better; a lift range that
includes 0, or a preference range that includes 50%, is not a result.

## Improve a skill against it

Read the judge's `why` for each eval the skill lost in `bench-results/results.json`, fix the
skill rather than the eval, and rerun the same command.

```bash
python3 run_bench.py --backend claude-cli --skills adr-generator --trials 2 \
  --second-judge claude-opus-5-5 --budget 5
```

Responses are cached, so only the edited skill's runs are paid for; add an eval the skill
hasn't seen before you trust the new number.

## Publish the result

Write the summary, without the outputs, to the file the site reads.

```bash
python3 run_bench.py --backend claude-cli --second-judge claude-opus-5-5 \
  --publish docs/benchmarks/latest.json
```

The [How skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) page and the
home page show it.
