---
rfc: 0056
title: A search command, and the CLI tested on Windows
status: implemented
date: 2026-10-20
author: sanjay-ananth
---

# RFC-0056: A search command, and the CLI tested on Windows

## Problem / use case

Two distribution gaps:

- **No way to find a skill from the terminal.** With 104 skills, `skilldrop list` prints names
  a newcomer can't map to their job. The site has full-text search; the CLI, which is what a
  person in Cursor or Codex has open, does not. `search` was in the CLI design doc and never
  built.
- **The CLI has never run on Windows.** It was written and tested on macOS and Linux, and
  nothing checked the parts that differ on Windows:
  - path separators, and the user's home folder;
  - `git` calls;
  - file permissions;
  - CRLF line endings in a Windows checkout;
  - the Python that skills' scripts run under.

## Fit check

Two new top-level files: `cli_smoke.js` and `.github/workflows/cli.yml`. The smoke test sits
at the root beside the repo's other tools. It is not in `package.json` `files`, so it doesn't
ship. Golden rules hold: zero dependencies, nothing executed from a catalogue, offline.

## Proposal

**`skilldrop search <words>`** searches skills, loops, agents and packs, offline, in the
catalogue in use (`--from` works).

- **Matching:**
  - Words match by prefix, so "deploy" finds "deployment".
  - Filler words like "why" or "my" are dropped.
  - Every word must match. When nothing does, entries matching some words are shown, and
    the reply says so.
- **Weighting**, highest first:
  - the name;
  - the tags;
  - the pack or outcome;
  - the description and the phrasings the skill's own trigger evals route to it. Those are
    how people actually ask: "why did our conversion drop" finds `hypothesis-comparison`,
    whose description never says "conversion".
- **Retired skills:** searching for one by name prints its retirement note (RFC-0046).
- **Output:** `--kind`, `--limit` and `--json` shape the results. The reply ends with the
  install command for the top match.

**`cli_smoke.js`** runs the CLI the way a user does: 16 checks, each a real
`node bin/skilldrop.js …` call in a throwaway folder or git repo. HOME and USERPROFILE point at
a throwaway home. The checks cover:

- validate, scan, list and search;
- install, diff, update and uninstall with `--dest`;
- a pack and a loop;
- `--project` for Claude Code and Cursor;
- `--local`, checking that `git status` stays clean;
- an agent;
- the `--contain` dry-run;
- a policy refusal that writes nothing;
- `loop-stats` with `--html`;
- `init-catalogue`, `new-skill` and `validate --from`;
- `package`, then `verify-mirror`, which catches a tampered file;
- `inventory`;
- one skill script under the OS's own Python.

**`cli.yml`** runs it on `ubuntu-latest`, `windows-latest` and `macos-latest` on every pull
request, and runs `validate.py` on each. It uses each runner's own Node and Python, so there
is no setup action to pin.

**What Windows found, fixed here.** Every smoke check passed on Windows the first time, but
`validate.py` didn't start. Python on Windows reads a file opened without an encoding as
cp1252, and the first em-dash in a SKILL.md stops it. The same mistake was in 45 `open()`
calls across 11 files, five of them skill scripts users run: `brand-kit`, `marketing-flyer`,
`deck-builder`, `ai-usage-report` and `pre-merge-review`. Each now names UTF-8, and those
skills get a patch release. `validate.py` now fails any repo or skill Python that opens text
without an encoding, so the mistake can't come back.

## Alternatives considered

- **Search over SKILL.md bodies too.** Every skill mentions reviews, plans and documents, so
  the ranking drowns. The description and the trigger phrasings say what a skill is for.
- **A shell-script smoke test.** It would need one copy in bash and one in PowerShell. A Node
  script runs the same on all three, with the same runtime the CLI uses.
- **Set `PYTHONUTF8=1` in CI.** CI would pass while the bug stayed on every Windows user's
  machine.

## Decision

Accepted and implemented in 0.16.34.
