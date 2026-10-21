---
rfc: 0062
title: Fuzzing the skill scripts that parse users' files
status: implemented
date: 2026-10-21
author: sanjay-ananth
---

# RFC-0062: Fuzzing the skill scripts that parse users' files

## Problem / use case

The skills' scripts read what a user hands them: SQL, Lighthouse and Terraform JSON, brand
files, cost and tracker exports, risk registers, event contracts and bundle stats. Writing unit
tests for them (RFC-0060) found about 35 inputs that crashed with a traceback where the script
should have rejected them clearly. Each of those was a shape someone had thought to try. A
fuzzer tries the shapes nobody thought of.

OpenSSF Scorecard also scores fuzzing. It detects Python fuzzing by an `import atheris` in the
repository.

## Fit check

No skill changes beyond fixing what the fuzzer finds. The targets live in `tests/fuzz/`, outside
every skill folder, and Atheris is a CI-only tool installed from a hash-locked file. The
published package still has no dependencies.

## Proposal

**Targets.** [`tests/fuzz/targets.py`](../../tests/fuzz/targets.py) lists 15 of them.
- Each runs one script as a user does, with the fuzzed bytes as the file it reads, starting from
  small valid seed inputs.
- A run passes when the script succeeds or rejects the input with an exit code it documents.
- Any other exception is a crash.

**Two engines, one set of targets.** [`tests/fuzz/fuzz.py`](../../tests/fuzz/fuzz.py) has both:
- **Atheris** (libFuzzer for Python), coverage-guided. It runs in CI on Linux, the only platform
  with Atheris wheels.
- **A small standard-library mutator.** It inserts structure, separators, NUL and invalid UTF-8
  bytes, and BOMs, and truncates, deletes and splices. It runs anywhere.

A crash saves its input, and `--replay` reproduces it.

**Where they run**
- `.github/workflows/fuzz.yml` runs every target, 20 seconds each, on pull requests and pushes
  that touch a script or the targets.
- It runs 120 seconds each on a weekly schedule.
- A crash fails the job and uploads the inputs.
- `tests/test_fuzz_targets.py` runs each target's seeds and 150 fixed mutations in the normal
  unit tests, on Linux, macOS and Windows.

**Atheris** is pinned by hash in `.github/tools/requirements-fuzz.txt`, and Dependabot keeps it
current.

**What it found on its first runs**
- **Five scripts crashed on a file that isn't valid UTF-8:** `risk-register`,
  `event-contract-draft`, `bundle-size-review`, `feedback-synthesis` and
  `hypothesis-comparison`.
- **`risk-register` crashed on a stray carriage return in a field.**
- **On Python 3.9 only, five CSV readers crashed on a NUL byte,** which the csv module rejects
  before Python 3.11: `cloud-cost-review`, `backlog-triage`, `team-status-report`,
  `feedback-synthesis` and `hypothesis-comparison`.

All now fail with a one-line message. After the fixes, every target ran 6,000 mutated inputs on
both Python 3.9 and 3.14 without a crash.

**What Atheris's first CI run then found** (20 seconds a target, coverage-guided)
- **`md-to-html` crashed on NUL bytes in Markdown.** They collided with its own placeholder
  markers.
- **`web-performance-review` crashed on a numeric field given as a string.**
- **`bundle-size-review` crashed on a list where a chunk id belongs.**

**The fix for wrong-shape JSON.** Coverage-guided fuzzing keeps finding JSON that parses but has
the wrong shape. So the six scripts that read JSON turn a `KeyError`, `TypeError`,
`AttributeError`, `IndexError` or `ValueError` at their entry point into one error. It names
what was expected, and says to report the file if it is genuine. The guard only changes how an
unhandled error is reported: the message still names the exception and its text, so a real bug
on a valid file can still be traced.

## Alternatives considered

- **OSS-Fuzz or ClusterFuzzLite.** Both are built for compiled projects and need a Docker build.
  A dozen stdlib Python parsers don't need that machinery. Atheris in a plain job is the same
  fuzzer.
- **Property tests with Hypothesis.** It's a good library, but a dependency for every test run.
  The unit tests stay stdlib-only.
- **A required check.** The fuzz job runs on time, not to a fixed end, so a slow runner could
  make it flaky. It reports, and the unit tests carry each fixed crash forward.

## Decision

Accepted and implemented in 0.16.45.
