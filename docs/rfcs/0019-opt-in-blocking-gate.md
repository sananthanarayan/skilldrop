---
rfc: 0019
title: Opt-in blocking gate — a deterministic git-hook harness
status: accepted   # draft → accepted | rejected → implemented
date: 2026-08-03
author: sananthanarayan
---

# RFC-0019: Opt-in blocking gate — a deterministic git-hook harness

## Problem / use case

`pre-merge-review` (RFC-0018) renders a `READY / NOT READY` verdict, but the verdict is prose an
agent can ignore — the gate is discipline, not mechanism. The question was whether skilldrop can
give the gate *harness*-grade enforcement (like agent-ready-repo's `work-loop`) while staying
portable across Claude Code, Cursor, Codex, and Aider. It can — but only by moving enforcement out
of the (portable, ignorable) skill file into the **substrate every tool shares: git and CI**. A
portable skill can never physically block an agent; a git hook and a CI required-check can.

## Fit check (structural change)

Golden rules / conventions touched:

- **RFC-0006 (hooks are reminders, not execution).** This adds an **opt-in** exception, scoped
  narrowly. RFC-0006's caution was about the CLI silently wiring an *AI pass* to run on your events.
  This is different in kind: a **deterministic lint/test gate**, installed only by an explicit
  operator command (`gate.py --install-hook`), never by a plain skill install. Running deterministic
  checks is exactly what git pre-commit hooks are for. The CLI's manifest-declared `hooks` (RFC-0006)
  stay reminder-only and unchanged; this is a separate mechanism a script offers, not a new manifest
  hook event.
- **Portability (golden premise).** Preserved and reinforced — the enforcement point is git, which
  all four tools use, so one mechanism works everywhere. No per-tool code is required for Layers 1–2.
- **No secrets / no repo ownership.** The hook runs the *operator's own* commands; it writes only a
  marker-fenced block into `.git/hooks/pre-commit` (idempotent, composes with existing hooks,
  removable via `--uninstall-hook`). skilldrop still doesn't own the user's repo.

## Proposal

Three enforcement layers, documented in `pre-merge-review` and implemented where skilldrop owns code:

1. **Layer 1 — blocking git pre-commit hook (implemented).** `gate.py --install-hook [--cmd/--config]`
   writes a marker-fenced `pre-commit` block (resolved via `git rev-parse --git-path hooks`, so it is
   worktree- and `core.hooksPath`-safe) that runs the gate and `exit 1`s on RED — git blocks the
   commit for *any* tool. `--uninstall-hook` removes just that block. Honest limit stated in-tool:
   `git commit --no-verify` bypasses it, so Layer 1 stops honest mistakes, not a determined override.
2. **Layer 2 — CI required status checks (documented pattern).** The same commands as a required
   check on the branch — un-bypassable server-side, tool-agnostic. The backstop `--no-verify` can't
   skip. (skilldrop itself already runs this via its `protect-main` ruleset.)
3. **Layer 3 — per-tool native hooks (documented).** Claude Code `Stop`/`PreToolUse` hook; Aider
   `--auto-test --test-cmd`. Richer UX where a tool can block its own turn; Cursor/Codex lean on 1–2.

Anti-patterns this bans: claiming a portable skill file can itself enforce a gate; installing a
blocking hook silently on a plain skill install (it is always an explicit `--install-hook`).

## Alternatives considered

- **Make the reminder hooks (RFC-0006) blocking by default.** Rejected — it would silently change
  behaviour on install and re-open the "hooks run things unasked" concern RFC-0006 closed. Opt-in via
  an explicit flag keeps the default safe.
- **Vendor `gate.py` into the repo and reference it relatively.** Deferred — the hook references the
  gate at its absolute install-time path (simple, no repo pollution); re-run `--install-hook` after
  moving/reinstalling. A `--vendored` copy-into-repo mode can follow if durability demands it.
- **Convert skilldrop into a harness repo.** Rejected (separate discussion) — it would trade
  skilldrop's portability and breadth for something agent-ready-repo already is. This RFC gives the
  *enforcement* benefit by composition (portable skill + the user's own git/CI), without the
  identity change.

## Decision

Accepted and implemented: `gate.py` gains `--install-hook` / `--uninstall-hook` (functionally tested —
a RED gate blocks the commit, `--no-verify` bypasses, uninstall is clean); `pre-merge-review` gains an
"Enforce as a harness (opt-in)" section documenting all three layers and the honest limit. skilldrop
stays a portable catalog; users opt into a real, portable, un-bypassable-at-CI harness in their own
repos.
