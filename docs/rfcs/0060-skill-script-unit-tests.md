---
rfc: 0060
title: Unit tests for every skill script
status: implemented
date: 2026-10-21
author: sanjay-ananth
---

# RFC-0060: Unit tests for every skill script

## Problem / use case

43 skills ship 48 Python scripts, about 27,000 lines. They compute the numbers a skill's answer
rests on: SLO burn rates, canary sample sizes, golden-diff verdicts, SQL lint findings,
bundle sizes and plan risks. Until now they were exercised only through the evals. Those cost
money to run, so they don't run on every change, and they test the skill's answer rather than
the script. A regression in a script could ship unseen, and nothing showed an engineer reading
the repo that the code was tested.

## Fit check

No skill folder changes. Tests live outside the skills in a new top-level `tests/` folder, so
copy-installing a skill still copies only the skill. They use only the standard library and
run offline, so CI needs nothing installed.

## Proposal

**The tests**
- `tests/test_<skill>.py`, one file per skill with scripts, written with `unittest`.
- [`tests/support.py`](../../tests/support.py) loads a script as a module, or runs it as a
  command, from its skill folder.
- 1,317 tests in all.
- They need no network, no packages and no external tools:
  - a script that needs `python-pptx`, `mmdc`, `pdftotext` or `tesseract` gets its other
    tests run and the rest skipped;
  - the Figma scripts are tested against a fake `requests` module.

**Running them**
- `.github/workflows/cli.yml` runs them on Linux, macOS and Windows, inside the smoke jobs that
  `protect-main` already requires.
- They pass on Python 3.9 and 3.14 locally.

**Keeping them complete:** `validate.py` fails when a skill has scripts but no test file, or when
its test file doesn't name one of the scripts.

**Known bugs:** a bug the tests found is recorded as `@unittest.expectedFailure` with a `# BUG:`
line. The test asserts the correct behaviour, so it starts passing when the script is fixed,
and `unittest` then reports it as an unexpected success.

**Writing the tests found 60 bugs in 34 skills:**
- **About 25 give wrong results.** For example:
  - AWS spot compute is always $0;
  - `--sprint "Sprint 1"` matches "Sprint 14";
  - a Markdown hard line break is joined into one word in Confluence output;
  - `safari > 15.3` is read as Safari 16;
  - a 31-day range is reported as 30 days;
  - a 500-line SKILL.md is counted as 501.
- **The rest crash with a traceback on input the script should reject clearly:** a JSON list
  where an object belongs, a non-UTF-8 file, or a header-only CSV.

They are fixed in follow-up changes, each removing its `expectedFailure`.

## Alternatives considered

- **pytest.** It's nicer to write, but it's a dependency. The repo's tools are stdlib-only, and
  `unittest` runs on every Python a user has.
- **Tests inside each skill folder.** They would ship to every user who installs the skill.
  They would also trip the rule that every file in a skill is referenced from its `SKILL.md`.
- **Fix the bugs before adding the tests.** The tests are how the bugs were found and how a fix
  is proved. Shipping them first records the bugs where anyone can see them.

## Decision

Accepted and implemented in 0.16.43.
