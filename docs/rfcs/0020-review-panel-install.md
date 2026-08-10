---
rfc: 0020
title: Review panel — one-command install + native parallel orchestration
status: implemented
date: 2026-08-05
author: sananthanarayan
---

# RFC-0020: Review panel — one-command install + native parallel orchestration

## Problem / use case

Multi-agent orchestration is now table stakes across the tools skilldrop targets — Claude Code
subagents, OpenAI Codex's parallel multi-agent runner, Google Antigravity's lead→specialist
delegation. skilldrop already has the *pieces* of a production-grade review panel (the three
reviewer subagents `devils-advocate` / `security-reviewer` / `code-quality`, installable into five
tools via RFC-0012; the `pre-merge-review` orchestrator skill that dispatches them; RFC-0017). But
two gaps kept it from being a first-class "fire the fleet" experience:

1. **No one-command install of the panel.** Standing up the panel meant three `--agent` installs
   plus a skill install — four commands, easy to get partial.
2. **No per-tool statement of how the panel fires in parallel.** The panel skills say "dispatch in
   parallel where subagents exist," but nowhere mapped that to each tool's native mechanism.

## Fit check (structural change)

Golden rules / conventions touched:

- **No new primitive, no fabricated formats.** A "panel" is just a named bundle of existing
  primitives (three agents + one skill). The CLI installs them through the *existing* agent and
  skill projections — it does **not** emit any tool-specific orchestrator config, because skilldrop
  never ships a format it can't verify (Codex/Antigravity native multi-agent config is not
  confirmed). The **orchestrator is the portable `pre-merge-review` skill**; the reviewers are the
  **native subagents** each tool already understands.
- **Portability preserved.** The panel installs where a tool has *both* a subagent and a skill
  format (Claude Code default/`--project`, Kiro, or `--dest`); for tools whose two targets diverge,
  the CLI refuses with an exact per-half command rather than a partial install.
- **CLI public surface changes** (a new `--panel` flag) → a **minor** version bump per AGENTS.md.

## Proposal

1. **`skilldrop install --panel review`** (implemented in `bin/skilldrop.js`). Installs the three
   reviewer subagents + the `pre-merge-review` skill in one command, delegating to `installAgents` +
   `install` so every existing safety/craft gate applies. Panels are defined in a small in-file
   `PANELS` map (one today: `review`); refuses `--ide` values whose agent and skill targets diverge,
   naming the two separate commands to run instead.
2. **Per-tool orchestration mapping** (in `agents/README.md`). A table: Claude Code (native parallel
   subagents), Kiro (native), Codex (multi-agent runner — verify invocation), Antigravity
   (lead→specialist delegation), Copilot (sequential unless it exposes parallel), Cursor (inline
   lens-sweep, no subagents). The orchestration lives in the skill; the reviewers are native
   subagents.
3. **No change to `subagent-design`** — it already documents the parallel / judge-panel topology the
   review panel instantiates; the mapping cites it.

Anti-patterns this bans: emitting an unverified per-tool orchestrator config; a partial panel install
that lands the agents but not the orchestrator (or vice versa).

## Alternatives considered

- **Emit a native orchestrator config per tool** (a Codex multi-agent file, an Antigravity lead-agent
  config). Rejected for now — those formats aren't confirmed, and shipping a fabricated one violates
  the "never invent a format" rule and would silently break. Revisit per-tool once each format is
  verified; the portable skill + native subagents already deliver the parallel dispatch where the
  runner exists.
- **A `panels.json` file + `validate.py` checks** (mirroring `packs.json`). Deferred — one panel
  doesn't earn a new top-level file and a new validation surface; the in-file `PANELS` map is
  enough. Extract to `panels.json` if panels multiply.
- **A dedicated `skilldrop panel` command.** Rejected — `install --panel` reuses the install target
  flags (`--project` / `--dest`) and the existing gates for free.

## Decision

Accepted and implemented: `install --panel review` installs the fleet in one command (functionally
tested — three agents + the orchestrator skill land together; unsupported `--ide` refused cleanly);
`agents/README.md` maps native parallel dispatch per tool. skilldrop's reviewer panel is now a
one-command install that fires natively-in-parallel where the tool supports it — portable orchestrator
skill, native subagents — without inventing a format. This is a **minor** release (new CLI flag).
