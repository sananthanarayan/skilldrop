---
rfc: 0009
title: AGENTS.md generator
status: draft
date: 2026-07-26
author: sananthanarayan
---

# RFC-0009: AGENTS.md generator

## Problem / use case

`AGENTS.md` stopped being a convention and became infrastructure: stewarded by the Linux Foundation's Agentic AI Foundation, read natively by Claude Code, Codex, Cursor, Copilot, Gemini CLI, Aider, Windsurf, Zed, Jules, Kiro and 20+ other tools, and present in 60,000+ repositories. A team adopting agentic coding now writes one whether they know how or not.

Most are bad in a specific, diagnosable way. They ask the agent to "write clean code" and "follow best practices" — instructions that consume context and change nothing — while omitting the four things that actually reduce ambiguity: the real commands, the real paths, the forbidden actions, and the conventions an agent would otherwise guess wrong. The published field guidance converges on the same shape: under ~150 lines, hand-verified commands, concrete examples, named prohibitions.

The failure mode that makes these files *worse than nothing* is an invented command. An `AGENTS.md` that says `npm test` in a repo with no test script sends every agent down a path that fails, and the agent will trust the file over the filesystem. This repo already knows that — golden rule 4 exists because of it.

skilldrop has no skill that produces one. `reverse-architecture` reads a repo but emits architecture; nothing emits agent policy.

## Fit check

- **Concrete artifact:** an `AGENTS.md` at the target repo root (plus, on request, the thin `CLAUDE.md` pointer this repo uses).
- **Portable:** reads a repo with ordinary file tools; no scripts, no API, no IDE dependency.
- **Opinionated:** every command in the output must trace to evidence in the repo — a `package.json` script, a Makefile target, a `pyproject.toml` entry, a CI workflow step — or it is omitted with a `[missing: no verified command]` marker. Never guessed, never inferred from ecosystem convention. Hard cap of ~150 lines. Generic virtue instructions ("be thorough", "write clean code") are stripped, not softened.
- **Category:** `Agent engineering`.

## Proposal

- **Name:** `agents-md-generator`. Tier `standard` (repo inspection + synthesis — same shape as `reverse-architecture`; no adversarial judgment). Packs: `dev-team`, `solution-architect`.
- **Two modes, one skill:** *generate* (no `AGENTS.md` present) and *audit* (one exists — score it against the bar, emit a diff, never silently rewrite a hand-tuned file).
- **Method:** inventory the repo's real command surface from manifests and CI → derive file placement from the actual tree → extract conventions worth stating (naming rules, invariants that a reasonable agent would break) → name forbidden actions → assemble under the line cap, dropping the lowest-value sections first when over.
- **Evidence rule:** every command carries its provenance internally during generation, so the audit mode can flag any line it cannot trace.
- **`related`:** `reverse-architecture` (upstream — its output is good input for the conventions section), `runbook-generator` (the human-operator sibling; different reader, different artifact).
- **Quality bar (sketch):** ≤150 lines; zero unverified commands; forbidden actions named explicitly; a newcomer agent could run the build and the tests from this file alone.
- **Anti-patterns to ban:** invented commands; generic virtue instructions; restating what the README already says; a file so long the agent's context is spent before the user's prompt arrives.

## Open questions for review

1. **Audit mode in the same skill, or a `doc-critique` rubric?** `doc-critique` already reviews documents against per-archetype rubrics in `rubrics/`. An `AGENTS.md` rubric there may be the cheaper half of this proposal — but the audit needs to *read the repo* to verify commands, which is outside `doc-critique`'s document-only intake. Current lean: keep audit here, because the evidence check is the whole point.
2. **Does it also emit the per-IDE satellites** (`CLAUDE.md` pointer, `.cursor/rules/`, `.github/copilot-instructions.md`)? Emitting one canonical file plus thin pointers matches how this repo does it, but the satellite formats overlap the CLI's projection layer (RFC-0006). Current lean: emit `AGENTS.md` + an optional `CLAUDE.md` pointer only; leave IDE projection to the CLI.
3. **Line cap as a hard fail or a warning?** ~150 lines is the published guidance; this repo's own `AGENTS.md` is well over it and is arguably right to be. Current lean: cap applies to generated files, audit mode reports the overage with the sections it would cut rather than failing.

## Alternatives considered

- **A template in `guide-builder`:** rejected — the value is the repo evidence check, not the layout. A template with no verification reproduces the invented-command failure.
- **A rubric in `doc-critique` only (audit, no generate):** partially rejected — see open question 1. It covers the "my file is bad" case but not the "I have no file" case, which is the larger population.
- **A script that greps for scripts:** rejected — the mechanical half is easy; deciding which conventions are worth a line of an agent's context is judgment, which is what a skill is for.
- **Do nothing:** rejected — it is the single most-installed agent artifact in the industry and the catalog is silent on it.

## Decision

{Pending review.}
