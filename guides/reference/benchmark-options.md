---
title: Benchmark options and report
summary: What run_bench.py needs, its flags, how each run is isolated, what it writes, and what each number in the report means.
kind: reference
---

# Benchmark options and report

This page is the detail behind [Benchmark skills against the agent without them](../how-to/benchmark-skills.md).
A skill's acceptance evals say what a good result looks like; they don't say whether the agent
would have got there without the skill. `run_bench.py` runs every eval twice, once with the
skill and once without, and compares the two.

## What it runs against

It runs against the catalogue in the clone it sits in. To benchmark your own skills, put them
in a pack folder in a clone (`packs/<pack>/skills/<name>/` with `evals/evals.json`) and run it
there.

## What you need

- A clone of the repository, and Python 3.9 or newer. The script has no dependencies.
- For `--backend claude-cli`: a signed-in Claude Code (`claude` on your `PATH`). Each run is a
  `claude -p` session, so it draws on your Claude Code plan and needs no API key.
- For `--backend api` (the default): `ANTHROPIC_API_KEY`. It makes one Messages API call per
  arm with no tools, so it suits only a skill whose work is all in the reply.

## Flags

Every flag, from `python3 run_bench.py --help`:

| Flag | What it does | Default |
|---|---|---|
| `--skills a,b` | Comma-separated skill names | all |
| `--held-out` | Only the evals flagged `held_out`, written by someone who never read the skill | off |
| `--evals 6,7` | Comma-separated eval ids, within each skill. Use it to run only evals a revision has never seen | all |
| `--models` | Comma-separated tiers from `model-routing.json` (`light`, `standard`, `heavy`) or model ids | `standard` |
| `--backend` | `api` or `claude-cli` | `api` |
| `--judge-model` | The model that grades and makes the blind comparison | `claude-sonnet-5-5` |
| `--second-judge MODEL` | A second model makes the same blind comparison; the report says how often the two agree | off |
| `--trials N` | Runs per eval per arm | 1 |
| `--budget USD` | Hard stop in dollars at list price for this run | 5 |
| `--tolerance` | Routing check: a model within this of the best score counts as adequate | 0.05 |
| `--workers` | Parallel workers | 4 |
| `--no-floor` | Skip grading the non-answer | off |
| `--dry-run` | Print how many agent sessions and judgements the run needs and a rough cost at list price; spend nothing | off |
| `--out DIR` | Directory for `results.json` and `report.md` | `bench-results` |
| `--publish FILE` | Also write the summary, without the outputs, to `FILE` | off |

Use `--trials 2` or more. One trial can't tell an improvement from noise: in the catalogue's
own runs the blind winner changed between two identical trials in about a third of evals.

## How each run is isolated

With `--backend claude-cli`, each arm is a Claude Code session with file and shell tools, in an
empty temporary directory, inside the operating system sandbox: no writes outside that
directory and no network. Your settings, plugins and MCP servers are not loaded. The skill arm
gets the skill's folder; the other arm is plain Claude Code. An eval whose prompt names input
files gets them from `evals/files/<eval id>/`, in both arms.

Because there is no network, a skill that has to install a dependency or call an API can't
finish, and will score worse than it would on your machine.

## What it writes

- `bench-results/report.md` — the report to read.
- `bench-results/results.json` — every output, grade and token count. For each pair the judge
  records a `why` that names the fault in the losing result.
- `.bench-cache/` — every response, so rerunning after you edit one skill pays only for that
  skill's runs.

## What each number means

| Number | What it is | How to read it |
|---|---|---|
| Assertions met | The share of the eval's assertions a judge marked met, for each arm | The skill's author wrote the assertions, so the arm without the skill is graded on a rubric it never saw. Expect a large gap. |
| Floor | What a non-answer scores | Assertions phrased "does not…" pass when nothing is written. Read both arms against it. |
| Preferred blind | The share of pairs where a judge that saw only the request and both results picked the skill's | 50% is no preference. This is the number that says whether the skill makes the result better, not only more compliant. |
| Ranges | 95% intervals over evals | A lift range that includes 0, or a preference range that includes 50%, is not a result. |
| $ per run | List price for the tokens each arm used | A skill with a script is often cheaper, because the script does the work. |

A skill with one eval gives you an anecdote. Three or more, with two trials, gives you
something to act on.

## Limits of a rerun after a fix

Fixes made after reading the judge's reasons are partly fitted to those evals. Add an eval the
skill hasn't seen before you trust the new number.

## Published summary and design

`--publish docs/benchmarks/latest.json` writes the file the site's
[How skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) page and home page
read. The design and its limits are in
[RFC-0040](../../docs/rfcs/0040-skill-benchmark.md); the rule that new skills are admitted on a
benchmark result is in [RFC-0041](../../docs/rfcs/0041-three-measured-skills.md).
