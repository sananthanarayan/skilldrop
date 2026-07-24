---
rfc: 0006
title: Per-IDE hooks with graceful degradation
status: accepted
date: 2026-07-24
author: sananthanarayan
---

# RFC-0006: Per-IDE hooks with graceful degradation

## Problem / use case

The loop-shaped skills (`feature-implement-loop`, loops built with `agent-loop-design`) would benefit from event-triggered automation the invoke-and-produce artifact skills don't need: a **pre-commit review gate** that runs `devils-advocate` before a commit lands, a **session-start primer** that tells the agent which skilldrop skills are installed and when to reach for them. Hooks are useful beyond Claude Code — Kiro has an agent-hooks system, and git hooks are IDE-agnostic — and users reasonably want the automation **customized to where they install**. skilldrop ships none today.

## Fit check

Structural change to the CLI, not the skills. It extends the per-IDE projection the CLI already performs (`--ide cursor` writes `.cursor/rules/*.mdc`, `--ide kiro` writes `.kiro/steering/*.md`). The portability premise holds because the split is deliberate: a skill carries a **neutral hooks declaration**, and the CLI emits the IDE-specific hook artifact at install time. The skill folder stays byte-identical across catalogs — the projection is the installer's job, never stored in the folder. `hooks` is a new **optional** manifest field, so existing skills and `validate.py`'s required-field check are unaffected.

The crux this RFC commits to: **graceful degradation, not parity.** Claude Code's hooks are agent-lifecycle events (`SessionStart`, `PreToolUse`, …); Kiro's are file-event/manual; Cursor, Continue, Cline, and Aider have no hook system. A neutral hook maps to the environments where it has a real target and is **skipped, with a printed note, where it doesn't**. Guaranteeing identical behavior everywhere is exactly the parity promise that forces agent-ready-repo's heavy projection engine — skilldrop declines it on purpose.

## Proposal

- **Optional `hooks` array in `manifest.json`.** Each entry `{ event, action, description }`, where `event` is drawn from a small neutral vocabulary and `action` names a skill to invoke or a command to run.
- **The CLI translates each hook to the most appropriate mechanism per install target**, and skips (printing what and why) where there is none. Coverage is per-event, not uniform per IDE. Starter vocabulary and mapping (illustrative; finalized during implementation):

  | neutral event | Claude Code | Kiro | git / other IDEs |
  |---|---|---|---|
  | `session-start` | `SessionStart` hook in `settings.json` | already covered by the steering wiring | skip |
  | `pre-commit-review` | `PreToolUse` matcher on the git-commit command | manual/on-demand agent hook | emit `.git/hooks/pre-commit` (IDE-agnostic) when a repo is present |
  | `on-demand` | slash-command entry | manual agent hook | skip |

  Note the honest asymmetry: `pre-commit-review` is often best served by an **IDE-agnostic git hook** rather than any IDE hook, and `session-start` in Kiro collapses into the steering file the CLI already writes. The CLI picks the mechanism that fits the event, not a single per-IDE format.
- **No shared state, no queues, no cross-skill coordination — event→action emission only.** This single constraint is the boundary between "customizable hooks" and "a runtime," and is the line the implementation must not cross.
- **`validate.py` gains two checks:** every hook `event` is in the known vocabulary, and every skill an `action` references exists.
- **v1 targets:** Claude Code + Kiro + git hooks. Codex is deferred until its mechanism is confirmed to fit (it is thinner than a full hook model). Cursor / Continue / Cline / Aider degrade to skip.
- **Trust (extends RFC-0003):** hooks run commands, so a hook from a third-party catalog inherits the review-before-use warning, and the CLI prints exactly which hook artifacts it wrote and where. Install still writes files only — it never executes a hook during installation.

## Alternatives considered

- **Parity across all IDEs (agent-ready-repo's projection engine):** rejected — the semantic gap between Claude Code's lifecycle hooks and Kiro's file-event hooks means parity requires the adapter + runtime machinery skilldrop exists to avoid.
- **Claude-Code-only optional hooks (the earlier position in this thread):** rejected as too narrow — Kiro and git hooks are real targets, and the CLI's projection layer already generalizes to more than one.
- **Store IDE-specific hooks inside the skill folder:** rejected — breaks byte-identical portability; the neutral-declaration + install-time-projection split is what preserves it.
- **Shared runtime with state/queues:** rejected — that is the agentbundle model and precisely what the "no runtime" constraint prevents.

## Decision

Accepted as design. Implementation — the manifest `hooks` schema, CLI emission per target with degradation, the two validator rules, and docs — is a follow-on PR that flips this to `implemented` and bumps the CLI minor version. Initial targets Claude Code + Kiro + git hooks; everything else degrades to a clean skip. The maintenance cost (a translator per hook-capable target, tracking format drift) is accepted as proportionate only for the loop-shaped skills that opt in; artifact-generator skills carry no `hooks` block.
