---
rfc: 0072
title: Keep, rebuild or retire the three skills that lost over both trials, and figma-diagrams re-run
status: implemented
date: 2026-11-04
author: sanjay-ananth
---

# RFC-0072: Keep, rebuild or retire the three skills that lost over both trials, and figma-diagrams re-run

## Problem / use case

The roadmap left four skills to decide after RFC-0068:
- `ai-usage-report`, `judge-audit` and `lean-canvas` lost to the plain agent over both
  scripts-only trials together;
- `figma-diagrams` needed a re-run, because the benchmark couldn't install its package.

The list was fixed before any judge's reason was read.

## Evidence

A third trial ran on each skill's held-out evals: two trials on `claude-sonnet-5-5`, with three
arms (the skill, its scripts only, the plain agent) and two blind judges. The cost was $22.88.
The earlier runs' outputs weren't kept on this machine, so the decisions rest on this run's
outputs, read in full by one analyst per skill, as RFC-0068 did.

| Skill | Pairs won against the plain agent (judge 1, judge 2) | Checks met: skill / scripts / plain | What the files showed | Rule it adds that the plain agent broke | Verdict |
|---|---|---|---|---|---|
| `lean-canvas` | 0, 0 of 4 | 88% / 62% / 62% | All three arms caught the same errors. The plain agent went further, for example on the cost of replacing lost customers. The skill's lead on checks was all on checks of its own format, which both judges called clutter. Its script's break-even left out that cost | None | **Retire**; use `business-case` for a costed decision |
| `ai-usage-report` | 1, 2 of 4 | 96% / 72% / 84% | The plain agent kept every rule the skill teaches: counts show activity, not quality; missing data is not zero; no leaderboard. The skill refused to rank when asked, hid names the manager had supplied, and named its own internals. Its script could read neither export | None. Its two wins came from the plain agent's data and arithmetic slips | **Retire** |
| `judge-audit` | 11, 8 of 16 | 73% / 60% / 61% | Wins came on evals the current version was revised against. On evals 10 and 11, which nothing was decided on, it won 1 and 0 of 4. In 7 of 16 runs its own script was held for approval and never ran | Report each run on its own, then name the items that flipped and which of them the experts label positive. The plain agent broke this in 4 of 4 runs of evals 7 and 11 | **Rebuild**, then re-measure |
| `figma-diagrams` | 3, 3.5 of 4 | 88% / 79% / 79% | With its package installed, the skill and the plain agent found the same problems. The skill kept to the format asked for, such as one line per comment, where the plain agent padded | Keeps the output to the shape the user asked for | **Keep** |

## Proposal

- **Retire `lean-canvas` and `ai-usage-report`** as RFC-0046 retires a skill.
  - The folder is deleted, and `catalogue.json` records why. `outdated`, `update` and `doctor`
    name an installed copy, with the reason and the uninstall command, and remove nothing.
  - The eight skills that listed `ai-usage-report` in `related` drop it. Each gets a patch
    bump.
  - The ai-engineering tutorial loses its last step, and the README's example now uses a
    held-out pair that `figma-diagrams` won.
- **Rebuild `judge-audit` rule-first, then measure it on fresh blind evals.** The rules:
  - **Repeated runs:** one row per run, then the flipped items by id, and which of them are
    positives.
  - **Limits:** one line on what the data can't measure, such as a single run or a single
    expert.
  - **The decision:** answer it as the user will actually run it, not a stricter stand-in.
  - **Extra labelling:** size it from how narrow the interval must be to settle the user's
    bar, never as a stock number.
  - **No tool:** if a tool can't run, count by hand and deliver. Never mention scripts,
    approvals or the run.
  - **Tone:** no capitalised verdict words.
- **Keep `figma-diagrams`.**

**What the benchmark itself got wrong, and what changes.**
- **Compound commands were held.** Claude Code holds a compound command (`python3 x.py; echo
  $?`) for approval even inside the sandbox, and a headless run has nobody to approve it.
  - The new flag `run_bench.py --allow-bash` allows every Bash command. The sandbox still
    blocks writes outside the working directory and all network.
  - It is off by default, so the tier trials in this change stay comparable with the first.
  - The `judge-audit` rebuild is measured with it. The next full run should make it the
    default and re-baseline.
- **A Python version blocked a package.** A skill whose package needs a newer Python than the
  benchmark's failed to install. The error now says so. `figma-diagrams` ran under Python 3.14.
- **A race in the shared environment.** Two workers building it raced on one temporary
  folder. It now has a per-thread name.

## Alternatives considered

- **Keep `judge-audit` on this run's 11 of 16.** The same version, model and evals scored 7.5
  and 7 of 16 on 27 October, and its wins came from evals it was revised against. That's noise
  around even, not a reversal.
- **Rebuild `ai-usage-report` around a better script.** The plain agent kept every rule
  without one, so a better script would serve a rule nobody breaks.

## Decision

Implemented on branch `sanjay-ananth/measure-loops-and-decide`. `judge-audit`'s rebuild is
next, and is not in this change.
