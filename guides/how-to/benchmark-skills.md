---
title: Benchmark skills against the agent without them
summary: Run each acceptance eval twice as an agent session, with the skill and without it, and read the lift, the blind preference from two judges, and the cost.
kind: how-to
---

# Benchmark skills against the agent without them

A skill's acceptance evals say what a good result looks like. They don't say whether the agent
would have got there without the skill. `run_bench.py` answers that: it runs every eval twice,
once with the skill and once without, and compares the two.

It runs against the catalogue in the clone it sits in. To benchmark your own skills, put them
in a pack folder in a clone (`packs/<pack>/skills/<name>/` with `evals/evals.json`) and run it
there.

## What you need

- A clone of the repository, and Python 3.9 or newer. The script has no dependencies.
- A signed-in Claude Code (`claude` on your `PATH`). Each run is a `claude -p` session, so it
  draws on your Claude Code plan and needs no API key.

## See what a run would cost first

```bash
python3 run_bench.py --backend claude-cli --dry-run
python3 run_bench.py --backend claude-cli --skills adr-generator,md-to-xlsx --dry-run
```

The dry run prints how many agent sessions and judgements the run needs and a rough cost at
list price. Nothing is spent.

## Run it

```bash
python3 run_bench.py --backend claude-cli --skills adr-generator --trials 2 \
  --second-judge claude-opus-5-5 --budget 5
```

- `--trials 2` runs each eval twice. One trial can't tell an improvement from noise: in the
  catalogue's own runs the blind winner changed between two identical trials in about a third
  of evals.
- `--second-judge` has a second model make the same blind comparison and reports how often the
  two agree.
- `--budget` is a hard stop in dollars at list price. The default is 5.

Results land in `bench-results/`: `report.md` to read, and `results.json` with every output,
grade and token count. Responses are cached under `.bench-cache/`, so rerunning after you edit
one skill pays only for that skill's runs.

## How each run is isolated

Each arm is a Claude Code session with file and shell tools, in an empty temporary directory,
inside the operating system sandbox: no writes outside that directory and no network. Your
settings, plugins and MCP servers are not loaded. The skill arm gets the skill's folder; the
other arm is plain Claude Code. An eval whose prompt names input files gets them from
`evals/files/<eval id>/`, in both arms.

Because there is no network, a skill that has to install a dependency or call an API can't
finish, and will score worse than it would on your machine.

## Read the report

| Number | What it is | How to read it |
|---|---|---|
| Assertions met | The share of the eval's assertions a judge marked met, for each arm | The skill's author wrote the assertions, so the arm without the skill is graded on a rubric it never saw. Expect a large gap. |
| Floor | What a non-answer scores | Assertions phrased "does not…" pass when nothing is written. Read both arms against it. |
| Preferred blind | The share of pairs where a judge that saw only the request and both results picked the skill's | 50% is no preference. This is the number that says whether the skill makes the result better, not only more compliant. |
| Ranges | 95% intervals over evals | A lift range that includes 0, or a preference range that includes 50%, is not a result. |
| $ per run | List price for the tokens each arm used | A skill with a script is often cheaper, because the script does the work. |

A skill with one eval gives you an anecdote. Three or more, with two trials, gives you
something to act on.

## Improve a skill against it

1. Read `results.json` for the evals the skill lost. The judge's `why` names the fault.
2. Fix the skill, not the eval.
3. Rerun the same command. Only the edited skill's runs are paid for.

Fixes made after reading the judge's reasons are partly fitted to those evals. Add an eval the
skill hasn't seen before you trust the new number.

## Publish the result

```bash
python3 run_bench.py --backend claude-cli --second-judge claude-opus-5-5 \
  --publish docs/benchmarks/latest.json
```

That writes the summary, without the outputs, to the file the site's
[How skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) page and home page
read. The design and its limits are in
[RFC-0040](../../docs/rfcs/0040-skill-benchmark.md); the rule that new skills are admitted on a
benchmark result is in [RFC-0041](../../docs/rfcs/0041-three-measured-skills.md).
