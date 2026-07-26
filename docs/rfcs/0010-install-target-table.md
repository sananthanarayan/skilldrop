---
rfc: 0010
title: Install-target table (splitting tool identity from install path)
status: draft
date: 2026-07-26
author: sananthanarayan
---

# RFC-0010: Install-target table (splitting tool identity from install path)

## Problem / use case

The 2026-07 survey in [`docs/designs/ide-primitive-coverage.md`](../designs/ide-primitive-coverage.md) established two facts the CLI's current shape cannot express:

1. **The tool→directory relationship is many-to-many.** Copilot CLI reads `.claude/skills/`, `.agents/skills/`, `.github/skills/`, and `~/.copilot/skills/`. `.claude/skills/` is read by both Claude Code and Copilot CLI. `.agents/skills/` is read by both Codex and Copilot CLI. Kiro IDE and Kiro CLI are one target sharing `.kiro/skills/`.
2. **The format is already identical everywhere.** Every surveyed tool reads a `SKILL.md` folder with `name` + `description` frontmatter. Nothing needs translating — only the directory differs.

Today `target()` in [`bin/skilldrop.js`](../../bin/skilldrop.js) maps one `--ide` value to exactly one hardcoded path, and three other functions branch on that same value independently: `wiringPath()` and `writeWiring()` (Cursor needs a `.mdc` pointer; nobody else does), and `emitHooks()` (only `claude` has a `session-start` target). Adding one tool means editing five sites — those four plus the help text — with no single place to check for a missed one.

The consequence is concrete and already visible. Two facts the survey found should have been a one-line change each, and neither is:

- `--project` writes `.claude/skills/`, which Copilot CLI reads. skilldrop supported Copilot CLI for months without knowing it, and could only *document* the coincidence (shipped in `0687d37`) rather than express it.
- Codex and Copilot need no format work at all, yet `--ide codex` cannot be added without a fifth copy of the same branch chain.

Three more targets are queued behind this (Codex, Copilot, plus Copilot's `.github/hooks/*.json` and Kiro's `preToolUse`). Writing them against the current shape means writing the branch chains three more times and then rewriting all of them.

## Fit check

Structural change to the CLI, not to skills. Touches golden rules 1 and 2 (skills are discovered by path; `skills/` doesn't move) and does not break them: skill folders stay flat and byte-identical, install remains a plain recursive copy, and every existing `cp -R` instruction in the README keeps working. It extends the projection layer RFC-0006 established rather than replacing it — the neutral hook vocabulary is unchanged, and this RFC adds **no** new events.

Explicitly **not** in scope: symlinking a canonical copy into each tool's directory (the pattern at least one competing multi-agent installer uses). It breaks the plain-copy portability premise, behaves badly on Windows, and makes `cp -R` and `skilldrop install` produce different results — which is the exact divergence skilldrop exists to avoid.

## Proposal

**Sharpen the claim first.** "`--ide <tool>` is the wrong design" is imprecise, and the imprecise version would delete something load-bearing. Tool identity is genuinely needed — Cursor needs a wiring file, Claude Code has a `session-start` target, and Codex/Copilot/Kiro each have native hook mechanisms worth emitting into later. What is wrong is that **`ide` does double duty**: it names a tool *and* hardcodes exactly one directory.

The change is to split those two axes and make the tool axis declarative:

- **One `TARGETS` table** describing each tool: its skills directory per scope (user / project), whether it needs a wiring file and which emitter writes it, and which neutral hook events it can service.
- **`target()`, `wiringPath()`, `writeWiring()`, and `emitHooks()` all read from that table** instead of carrying parallel branch chains. Adding a target becomes a table row.
- **Help text is generated from the table**, so the documented targets cannot drift from the supported ones.
- **New `skilldrop paths [tool]`** — reports which directories a tool reads and which already contain skills. This is how the many-to-many fact reaches the user without the CLI writing N copies.

`--ide claude | cursor | kiro` and `--project` keep their exact current behavior. `--dest <dir>` keeps meaning "copy only, no tool identity."

## Decisions this RFC must settle

Three real choices. Recommendations given; none is obviously forced.

### 1. Where does the ledger live?

`ledger(dest)` writes `.skilldrop.json` **inside** each destination directory. If a future `--ide copilot` wrote to more than one of Copilot's paths, there would be N ledgers for one logical install, and `update` / `outdated` / `uninstall` would have no authoritative answer when the same skill sits in two directories at different versions.

- **(a) One ledger per directory — recommended.** Already the shipped behavior. Survives a directory being deleted by hand, needs no special case for `--dest`, and never desyncs from the filesystem because it *is* the filesystem. Cost: `outdated` only sees the target you point it at.
- **(b) One central ledger** (`~/.skilldrop/installs.json`) recording every path. Enables a true `skilldrop outdated --all`. Cost: a second source of truth that goes stale the moment someone deletes a folder by hand, which is a thing people do.

### 2. Does one invocation write to multiple paths?

- **(a) One path per invocation — recommended.** `skilldrop paths` *reports* the other directories a tool reads; the user chooses. Predictable, and `uninstall` stays exact.
- **(b) Write every path the tool reads.** One command fully provisions a tool. Cost: N copies that drift, N ledgers (forcing decision 1b), and an `uninstall` that has to guess which copies were skilldrop's.

### 3. What happens to hooks when the path doesn't imply a tool?

`--dest .agents/skills` could be Codex or Copilot CLI; `emitHooks()` cannot tell.

- **Recommended:** `--dest` continues to mean copy-only — hooks skipped with a printed note naming what was skipped and why. This is exactly RFC-0006's degradation contract, not a new rule. Tool-specific hooks require `--ide`.

## Verification

This refactor touches install, update, uninstall, wiring, and hooks across every target, and **there is no test runner in this repo**. `validate.py` will not catch a regression here — it validates the catalog, not the CLI.

So the RFC commits to a **written manual test matrix** in the implementing PR: each target × {install, update, uninstall} × {with, without `--with-hooks`}, plus the two legacy-cleanup cases already verified for Kiro (skilldrop-authored shim removed, hand-written file kept). A fixture-based CLI test suite is worth having and is **deliberately left to its own RFC** — bundling it here would double the scope of a refactor that is otherwise mechanical.

## Alternatives considered

- **Add `--ide codex` and `--ide copilot` the current way, refactor later:** rejected — it means writing the five-site branch chain three more times and then rewriting all of them. The survey already established the shape is wrong; building against a known-wrong shape is the expensive order.
- **Drop `--ide` entirely, `--dest`-only:** rejected — it deletes tool identity, which Cursor's wiring file and every hook target depend on. It also pushes the many-to-many path table onto every user's memory, which is the problem this is trying to solve.
- **Symlink a canonical copy into each tool's directory:** rejected on Windows behavior and on the portability premise (see Fit check).
- **Auto-detect installed tools and offer targets:** deferred, not rejected — it is already listed as design-only in [`skilldrop-cli-design.md`](../designs/skilldrop-cli-design.md), and it becomes straightforward *once* `TARGETS` exists. Sequencing, not disagreement.
- **Do nothing:** rejected — three targets are queued behind this, and the first one written the old way sets the pattern for the rest.

## Decision

{Pending — the three decisions above are open. Nothing is implemented; `0687d37` documented the discovery paths as an interim measure.}
