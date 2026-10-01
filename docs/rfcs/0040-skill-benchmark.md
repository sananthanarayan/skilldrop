---
rfc: 0040
title: Skill benchmark with a no-skill baseline
status: implemented
date: 2026-10-01
author: sananthanarayan
---

# RFC-0040: Skill benchmark with a no-skill baseline

## Problem / use case

`run_evals.py --assertions` reports how many of a skill's assertions its output meets. That
number has nothing to compare against: it doesn't say what the same model does with no skill,
what the run cost, or whether a second run would give the same answer. A user deciding whether
to install a skill, and a maintainer deciding which model tier it needs, are both asking
"compared to what, at what cost?", and the catalogue can't answer.

## Fit check

A structural change: one new top-level file. It touches golden rule 4 (the only automated
checks are `validate.py` and `skilldrop validate`) and keeps it. The benchmark is report-only,
calls a paid API, and is never a merge gate.

## Proposal

`run_bench.py`, stdlib only, reusing `anthropic_api.py` and the grading in `run_evals.py`.

- **Paired arms.** Each eval in `evals/evals.json` runs twice per model: with the skill and
  without it. Same request, same model.
- **Agent runs, not single calls.** The first pilot ran one API call per arm with no tools. Both
  arms answered "I'll check the working directory" and stopped, and scored near zero. A skill is
  a set of instructions for an agent, so `--backend claude-cli` runs each arm as a Claude Code
  session (`claude -p`) with file and shell tools, in an empty directory, inside the OS sandbox
  (no writes outside it, no network), with no settings, plugins or MCP servers from the machine.
  The skill arm gets the skill's folder at `skills/<name>/`; the baseline is plain Claude Code.
  The run is graded on its final message and the files it left behind. It needs a signed-in
  Claude Code, not an API key. `--backend api` remains for skills whose work is all in the reply.
- **Input files.** An eval whose prompt names files keeps them in `evals/files/<eval id>/`.
  Both arms get them. 22 evals across 15 skills gained fixtures with this RFC.
- **A floor.** A non-answer is graded against every eval's assertions. 87 of the 773 assertions
  are phrased as "does not…", and they pass when nothing is written.
- **Two measures.** Assertions met, graded by a judge that doesn't know the arm; and a blind
  pairwise preference, where the judge sees the request and both outputs in a shuffled order
  with no assertions and no skill text. The second exists because the skill's author wrote the
  assertions.
- **Evals are the unit.** Lift is the paired difference per eval, with a 95% bootstrap interval
  over evals. `--trials N` repeats each eval and reports how far the score moves between runs.
- **Cost from the API.** Tokens come from each response's `usage` block and are priced at that
  model's rate. The judge's spend is recorded apart from the generation's.
- **Spend control.** `--budget` is a hard stop (default $5). `--dry-run` prints the call count
  and a rough estimate. Responses are cached under `.bench-cache/`, so a rerun is free.
- **The served model is checked** on every call; a mismatch is an error, not a score.
- **Routing check.** With more than one model, each skill's score per model is shown beside
  the tier `model-routing.json` assigns and the cheapest model within `--tolerance` of the best.

Output goes to `bench-results/` (`results.json` with every output, grade and token count, and
`report.md`). Both directories are git-ignored. `--publish docs/benchmarks/latest.json` writes
the summary without the outputs; that file is committed, and `build_pages.py` renders it on the
site's *How skills are checked* page.

Known limits, stated in the report and on the site: 69 of 93 skills have a single eval, so only
the catalogue-wide number carries weight; the skill's author wrote the assertions; the judge is
a model; the sandbox has no network, so a skill that needs to install a dependency or call an
API can't finish.

## Alternatives considered

- **Add `--baseline` to `run_evals.py`.** That file is the weekly, cheap, report-only run. The
  benchmark has different defaults (a budget, a cache, trials) and would double its size.
- **Assertions only, no pairwise judge.** Cheaper, but the baseline is then graded only on a
  rubric written from the skill's own rules, which overstates the lift.
- **Commit every run's full results.** Outputs run to megabytes. Only the summary is committed.

## Open questions

- More evals per skill, so a per-skill number means something.
- `md-to-docx` eval 2 and `eval-harness-generator` eval 1 describe pasted content instead of
  containing it. They need rewriting before they measure anything.
- Skills installed at user scope on the machine are visible by name to both arms.
