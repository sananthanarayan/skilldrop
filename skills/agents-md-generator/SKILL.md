---
name: agents-md-generator
description: Generate or audit a repository's AGENTS.md — the agent-policy file Claude Code, Codex, Cursor, Copilot, Kiro and Antigravity read — with every command traced to real evidence in the repo, generic virtue instructions stripped, and forbidden actions named. Use when a repo has no AGENTS.md, when an existing one is stale or ignored, when onboarding a codebase to agentic coding, or when an agent keeps running commands that don't exist.
---

# agents-md-generator

Produces the file agents read *before* the user's prompt. An `AGENTS.md` is not documentation — it is the context an agent spends on every turn, so a line that changes no decision is a line stolen from the task.

The failure that makes these files worse than useless is an **invented command**. `npm test` in a repo with no test script sends every agent down a path that fails, and the agent trusts the file over the filesystem. So the rule this skill is built around: **every command traces to evidence in the repo, or it does not appear.**

Two modes, chosen by what's already there:
- **Generate** — no `AGENTS.md` exists. Produce one under the line cap.
- **Audit** — one exists. Score it, name what can't be verified, emit a diff. Never silently rewrite a hand-tuned file.

## How to respond

1. **Inventory the real command surface before writing anything.** Read, in this order: `package.json` (`scripts`), `Makefile`, `pyproject.toml` / `setup.cfg`, `Cargo.toml`, `go.mod`, `composer.json`, `.github/workflows/*.yml`, `justfile`, `Taskfile.yml`, and any `CONTRIBUTING.md`. CI workflows are the highest-value source: they contain the commands that actually have to pass.

   For each command record its **provenance** — the file and key it came from. Provenance is what makes audit mode possible later.

2. **Apply the evidence rule without exception.** A command appears only if it traces to a file in the repo. Never infer from ecosystem convention: a Python repo does not necessarily run `pytest`, and a repo with `jest` in `devDependencies` may still have no test script.

   When a section needs a command that doesn't exist, write the marker, not a guess: ✅ *"Test: `[missing: no test script in package.json or CI]`"* — ❌ *"Test: `npm test`"*. The marker is useful; the guess is a trap.

3. **Derive file placement from the actual tree**, not from what the framework usually does. Name the directories that exist and what belongs in each. Two or three rows beat a full tree dump.

4. **Extract only conventions an agent would otherwise get wrong.** The test is counterfactual: *would a competent agent, without this line, do the wrong thing?* Naming rules that are enforced somewhere, invariants that look arbitrary but aren't, a generated file that must never be hand-edited. If the answer is no, cut the line.

   Generic virtue instructions — "write clean code", "be thorough", "follow best practices", "use good naming" — are **stripped, not softened.** They consume context and change no behaviour.

5. **Name forbidden actions explicitly.** This is the section most files omit and the one that prevents the most damage: paths that must not be touched, commands that must never run unattended, files that are generated, secrets that must never be committed. Concrete and few.

6. **Assemble under ~150 lines.** In generate mode this is a **hard cap** — go over and cut, lowest value first (background prose, then examples, then convention lines that failed the counterfactual test). In audit mode it is a **warning**: report the overage and name the sections you would cut, because an existing file may be long for good reason.

7. **Satellites only on request, and only as a delta.** If asked to wire a specific tool, emit a satellite (`CLAUDE.md`, `.github/copilot-instructions.md`, `GEMINI.md`) that contains **only what is specific to that tool**, plus one line pointing at `AGENTS.md` for everything shared. **Refuse to copy shared content into a satellite** — four copies of a command list is four chances to be wrong, and the drift is invisible. See [`reference.md`](reference.md) for the per-tool shapes.

8. **Emit.** Generate mode: the file, plus a provenance table showing where each command came from and what was marked `[missing]`. Audit mode: verdict, the unverifiable lines quoted, the virtue instructions to cut, the line-count position, and a concrete diff.

**Non-interactive runs:** unstated conventions are simply omitted — an `AGENTS.md` is allowed to be short. If the repo cannot be read at all, emit `BLOCKED: need repo access — every command must trace to a file`. Never produce an `AGENTS.md` from a description of a repo; the whole artifact is a claim about what is in the tree.

## Useful references in this skill

- [`reference.md`](reference.md) — where each tool looks, the evidence-source table, the satellite shapes, and the strip-list of virtue phrasings
- [`templates/agents-md.md`](templates/agents-md.md) — the output skeleton with the section order and the line budget per section

## Quality bar

- **Zero unverified commands.** Every one traces to a file and key, or carries a `[missing: …]` marker. This is the bar; a file that fails it is worse than no file.
- **A newcomer agent could build and test from this file alone** — or can see plainly that the repo has no such command.
- **Forbidden actions are named**, not implied.
- **Every convention line passes the counterfactual test.** If an agent would do the right thing without it, it is padding.
- **≤150 lines generated.** Over the cap means something was kept that should have been cut.
- **No virtue instructions survive.** Search the output for "clean", "best practice", "thorough", "appropriate", "as needed" — each hit is a line that changes nothing.
- **It does not restate the README.** Different reader, different job: the README sells and explains, `AGENTS.md` constrains.

## When to use this skill

- ✅ A repo is adopting agentic coding and has no `AGENTS.md`
- ✅ An existing `AGENTS.md` is stale, ignored, or full of advice rather than facts
- ✅ Agents keep running commands that don't exist in the repo
- ✅ Onboarding a legacy codebase where the real commands live only in CI
- ✅ After `reverse-architecture` — its extraction is good input for the conventions section

## When NOT to use this skill

- ❌ Writing human contributor docs — that's `CONTRIBUTING.md`, a different reader
- ❌ Explaining what the project *is* — that's the README
- ❌ Operating a running service — that's `runbook-generator`
- ❌ Reviewing an existing document's prose quality — that's `doc-critique`, which takes documents; this one takes a repository

## Anti-patterns to avoid

- ❌ **Inventing a command that "should" exist.** The single most damaging thing this artifact can do. A `[missing]` marker is a finding; a guess is a fault the agent will trust.
- ❌ **Virtue instructions.** "Write clean, maintainable code" is context spent on nothing. Agents already try.
- ❌ **Dumping the file tree.** Placement rules earn their space; a directory listing does not — the agent can run `ls`.
- ❌ **Restating the README.** If it's already there, link it.
- ❌ **A satellite that duplicates `AGENTS.md`.** Guaranteed drift, invisible until an agent acts on the stale copy.
- ❌ **Silently rewriting a hand-tuned file.** Audit mode emits a diff and lets a human choose; the file may encode decisions the repo can't show you.
- ❌ **Writing to the cap.** 150 lines is a ceiling, not a target. Most repos need far less.
