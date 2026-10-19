---
rfc: 0049
title: A guard that keeps the maintainers' own identity out of the repository
status: implemented
date: 2026-10-19
author: sanjay-ananth
---

# RFC-0049: A guard that keeps the maintainers' own identity out of the repository

## Problem / use case

The repository is public and two GitHub accounts commit to it. Two things can publish a
maintainer without anyone deciding to. A Claude Code session knows the signed-in account, and
a model writes that name into a document's Author field unasked: in the light and heavy tier
run (0.16.21), `design-doc` on Opus 5.5 wrote the maintainer's name as author three times,
once with no skill loaded at all. Git records whatever email a machine is configured with,
and one mis-set worktree is enough. Nothing checked for either. The history is clean today
(every commit on `main` uses a GitHub noreply address, and neither account shows a public
email), so this is a guard, not a clean-up.

## Fit check

Structural change: a new top-level file (`privacy.py`), a new top-level directory
(`.githooks/`), and a repo-wide convention. Golden rule 5 (no personal data) gains a check;
no skill's anatomy changes.

## Proposal

- **`privacy.py`** (stdlib) reads what to protect from the machine it runs on: the signed-in
  Claude account's name, email and organization, git config, the system user and home
  directory, plus `.skilldrop-private` (git-ignored) and `SKILLDROP_PRIVATE_TERMS`. The list
  is never written into the repository, and a match is reported by kind ("your account
  email"), never printed, so a log can't leak it. Terms match as whole words, and public
  GitHub handles are masked first, so a handle that contains a surname is not a leak. The
  maintainer's name is allowed only in the files that publish it on purpose.
- **Hooks** in `.githooks/` (turned on with `git config core.hooksPath .githooks`): the
  staged change, the commit message and the commit identity.
- **`validate.py`** runs the same scan over every tracked file.
- **CI** (`security.yml`) checks that every commit in a push or pull request has a GitHub
  noreply author and committer email. This needs no private data, so it guards both accounts
  whichever one pushes.
- **`run_bench.py`** counts outputs that name the signed-in user, redacts them in
  `results.json`, and refuses to `--publish` a summary that names them.
- The one template with an author field (`design-doc`) now says to take names from the brief.

## Alternatives considered

- **A list of names in a CI secret.** It would let CI scan content too, but it stores the
  personal details on GitHub to protect them from GitHub. The hooks scan content locally,
  where the details already are; CI checks only what needs no secret.
- **Strip the account from benchmark sessions.** Claude Code offers no documented way to run
  signed in without the session knowing the account, and inventing one breaks rule 4.
- **A rule in every skill.** The baseline did it too, so it is not a skill habit; one rule in
  AGENTS.md and the one affected template cover it.

## Decision

Implemented in 0.16.24. Replaying the tier run's saved results through the benchmark check
flags exactly the three `design-doc` runs found by hand.
