# agents-md-generator — reference

## Who reads what

Confirmed in the July 2026 survey ([`docs/designs/ide-primitive-coverage.md`](../../docs/designs/ide-primitive-coverage.md)). A root `AGENTS.md` is the broadest single file; satellites are a reach fix for specific tools, not the norm.

| Tool | Reads |
|---|---|
| Codex | root `AGENTS.md` |
| GitHub Copilot | root `AGENTS.md`, `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, and also root `CLAUDE.md` / `GEMINI.md` |
| Claude Code | `CLAUDE.md` (auto-loaded) |
| Cursor | root `AGENTS.md`, plus `.cursor/rules/*.mdc` for rules |
| Kiro | root `AGENTS.md`, plus `.kiro/steering/` for always-on context |
| Antigravity | root `AGENTS.md` |

**Precedence matters more than reach.** Several of these load on every turn regardless of relevance. A file that is always in context should carry only what earns its place there — the same reason an always-included steering file is a poor home for a persona.

## Evidence sources, in priority order

Every command must trace to one of these. Record the file and key as provenance.

| Source | What it proves |
|---|---|
| `.github/workflows/*.yml` (and other CI) | **Strongest.** These commands must pass or the build fails |
| `Makefile` / `justfile` / `Taskfile.yml` | Named entry points the team actually uses |
| `package.json` `scripts` | Node entry points; check the script body, not just the key |
| `pyproject.toml` / `setup.cfg` / `tox.ini` | Python entry points and runners |
| `Cargo.toml`, `go.mod`, `composer.json`, `Gemfile` | Ecosystem defaults *only if* the file confirms them |
| `CONTRIBUTING.md`, `README.md` | Human-facing; **verify against the above before trusting** — docs go stale faster than CI |
| Dev container / Dockerfile | Setup steps and version pins |

**A dependency is not a command.** `jest` in `devDependencies` does not mean `npm test` exists. Check for the script.

## What earns a line — the counterfactual test

Ask: *without this line, would a competent agent do the wrong thing?*

| ✅ Earns its place | ❌ Cut |
|---|---|
| "Generated — never hand-edit `src/api/types.ts`; run `make codegen`" | "Keep the codebase clean and well organised" |
| "Migrations are append-only; never edit a committed migration" | "Follow database best practices" |
| "Tests live beside the source as `*_test.go`, not in `tests/`" | "Write comprehensive tests" |
| "`main` is protected; open a PR" | "Follow good git hygiene" |
| "Do not run `terraform apply` — plan only, a human applies" | "Be careful with infrastructure" |

## Strip list

Search generated output for these; each hit is a line that changes no behaviour:

`clean` · `best practice` · `thorough` · `appropriate` · `as needed` · `where possible` · `make sure to` · `try to` · `robust` · `maintainable` · `readable` · `well-structured` · `properly` · `high-quality` · `idiomatic` (unless a specific idiom is named)

## Satellite shapes — delta only

A satellite carries what is specific to its tool **and nothing else**. Every shared fact stays in `AGENTS.md` and is pointed at.

**`CLAUDE.md`** — Claude Code auto-loads it:

```markdown
# CLAUDE.md

The substantive guidance lives in [AGENTS.md](AGENTS.md). Read it first.

This file exists because Claude Code auto-loads `CLAUDE.md`. Everything below is
Claude-Code-specific and does not belong in the cross-IDE file.

## <tool-specific section>
…e.g. `${CLAUDE_SKILL_DIR}` semantics, `.claude/settings.json`, subagent delegation…
```

**`.github/copilot-instructions.md`** — same shape, Copilot-specific content only (custom agents in `.github/agents/`, `.github/hooks/*.json`).

**`GEMINI.md`** — same shape, for Gemini/Antigravity specifics.

**Refuse** to emit a satellite containing the command table, file placement, or conventions that already live in `AGENTS.md`. If a tool needs those, it reads `AGENTS.md` — and if it genuinely cannot, say so plainly rather than duplicating.

## Line budget

150 lines total. A workable split:

| Section | Lines |
|---|---|
| Repo in one paragraph | 3–5 |
| Commands (with provenance verified) | 15–30 |
| File placement | 10–20 |
| Conventions that pass the counterfactual test | 20–40 |
| Forbidden actions | 5–15 |
| Pointers to deeper docs | 3–5 |

Over budget: cut background prose first, then examples, then convention lines that only *probably* pass the test.
