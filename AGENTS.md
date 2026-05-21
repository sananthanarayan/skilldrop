# AGENTS.md — Guidance for Autonomous Coding Agents

> Canonical guide for Copilot, Codex, Cursor, and other agentic IDEs operating on this repository.

## Repo in one paragraph

**skilldrop** is a collection of portable **Claude Skills** for the deliverables knowledge workers actually ship: diagrams, ADRs, design docs, runbooks, decks, decision logs, comparison matrices, exec summaries, structured critiques, and adversarial code review. Each skill is a plain directory under `skills/` containing a `SKILL.md` + `manifest.json` (+ optional `reference.md`, `templates/`, `lenses/`, `rubrics/`, `examples/`, `scripts/`, `requirements.txt`). Installation is per-folder copy into the target IDE's skills/rules location — documented per-IDE install steps live in `README.md` (Claude Code, Cursor, Kiro, Continue, Cline, Aider).

## Golden rules

1. **Folder name = `SKILL.md` `name` = `manifest.json` `name`.** Kebab-case, use-case-first, no version suffix. Changing any of the three without the others breaks slash-command invocation.
2. **Do not move** `skills/`, `CONTRIBUTING.md`, `MAINTAINERS.md`, `LICENSE`, or `README.md`. Skills are discovered by path; moving the directory breaks every install instruction the README documents.
3. **Keep `SKILL.md` under ~500 lines.** Spill into `reference.md`, `templates/`, `lenses/`, `rubrics/`, or `examples/`. Agent context is the binding constraint — a bloated `SKILL.md` crowds out the user's actual prompt.
4. **Never invent commands, env vars, or file conventions.** Use those documented below and in `CONTRIBUTING.md`. This repo has no test runner, no CI, no linter at the root — don't pretend it does.
5. **No secrets, no real customer names, no personal data** in templates, examples, or sample inputs. Placeholder data only.
6. **Voice is opinionated, not hedged.** Strip "generally", "consider", "you might want to". The `✅` / `❌` markers have semantic meaning — don't use them decoratively, don't add other decorative emoji.
7. **Every new skill ships with `Quality bar` and `Anti-patterns to avoid` sections.** A skill without them is a description, not a generator. Both are explicitly enforced by the PR checklist in `CONTRIBUTING.md`.
8. **Contributors do not merge to `main`.** PRs only, from a feature branch, merged by a maintainer. The maintainer bypass documented in `CONTRIBUTING.md` is for repo admins and does not extend to contributors.

## Verified commands (do not invent variants)

```bash
# Install a single skill into Claude Code — user-scope (every project)
mkdir -p ~/.claude/skills && cp -R skills/<skill-name> ~/.claude/skills/

# Install a single skill into Claude Code — project-scope (tracked with repo)
mkdir -p .claude/skills && cp -R skills/<skill-name> .claude/skills/

# Install Python deps for a skill that has them (currently figma-diagrams, deck-builder)
cd skills/<skill-name> && python3 -m pip install -r requirements.txt

# Branch + PR workflow (the only path to main for contributors)
git checkout -b feat/<short-kebab-name>      # or fix/… docs/… chore/…
git push origin feat/<short-kebab-name>
gh pr create --base main --head <handle>:feat/<short-kebab-name>
```

There is **no `make` target, no test command, no lint command, no CI gate** at the repo root. Quality assurance is the manual-test pass documented in `CONTRIBUTING.md` step 7: install the skill into a clean Claude Code session, run it end-to-end on a realistic input, and verify the output meets the skill's own quality bar.

## File placement

| Kind | Where |
|---|---|
| New skill | `skills/<kebab-name>/SKILL.md` + `skills/<kebab-name>/manifest.json` |
| Long-form reference for a skill | `skills/<skill-name>/reference.md` |
| Paste-able starter content | `skills/<skill-name>/templates/<name>.md` |
| Worked example (input → output) | `skills/<skill-name>/examples/<name>.md` |
| Adversarial-sweep checklist (devils-advocate style) | `skills/<skill-name>/lenses/<name>.md` |
| Per-archetype quality bar (doc-critique style) | `skills/<skill-name>/rubrics/<archetype>.md` |
| Executable helper | `skills/<skill-name>/scripts/<name>.py` (or `.js`, `.sh`) |
| Python dep manifest for a skill | `skills/<skill-name>/requirements.txt` |
| Claude Code project settings | `.claude/settings.json` — optional config (hooks, permissions, env). Inert for non-Claude tools. |
| Repo policy | `CONTRIBUTING.md`, `MAINTAINERS.md` |

Anything outside `skills/` is repo policy or hygiene. New top-level directories should be proposed in a PR with rationale, not added silently.

## SKILL.md frontmatter (required, exactly this shape)

```yaml
---
name: your-skill-name
description: One sentence, use-case-first. First half says *what it does*; second half states *when to use it* (the trigger phrases an AI agent will match on). This is the most-read string in your skill.
---
```

`name` must match the folder name **and** the `name` in `manifest.json`.

## manifest.json (required fields)

```json
{
  "name": "your-skill-name",
  "version": "0.1.0",
  "description": "Same shape as SKILL.md frontmatter — keep them in sync.",
  "entrypoint": "SKILL.md",
  "deps": { "npm": [], "pip": [] },
  "env": { "required": [], "optional": [] },
  "tags": ["tag1", "tag2", "tag3"]
}
```

If the skill has no scripts, leave `deps` empty. `env.required` is for vars the skill cannot work without (e.g. `FIGMA_TOKEN` for `figma-diagrams`); `env.optional` is for vars that change behaviour but aren't blockers.

## Before you commit

- [ ] PR is from a **feature branch**, not from `main`.
- [ ] Folder name = `SKILL.md` `name` = `manifest.json` `name`.
- [ ] `SKILL.md` is **≤ ~500 lines** — long material moved into siblings.
- [ ] `Quality bar` and `Anti-patterns to avoid` sections are present.
- [ ] At least one **worked example** for new diagram, deck, or review skills.
- [ ] Description **leads with the use case** and **ends with trigger phrases**.
- [ ] `README.md` updated — row added to **Skills in this repo**, and to **Installing dependencies** if the skill has runtime deps.
- [ ] **Manual test pass** — installed the skill into a clean Claude Code session and ran it on a realistic input. Output meets the skill's own quality bar.
- [ ] Scripts (if any) reference both `${CLAUDE_SKILL_DIR}/scripts/…` **and** a plain relative `scripts/…` so non-Claude IDEs can find them.
- [ ] No secrets, no real customer data — placeholder values only.
- [ ] Voice matches the established opinionated tone (see below).

## Voice & tone (non-negotiable)

The single most important section of `CONTRIBUTING.md` is **Voice & tone** — re-read it before drafting any `SKILL.md` content. The short version:

- ✅ Make decisions for the user. Pick defaults. Cap clarifying questions at 2.
- ✅ Lead with the rule, then the rationale.
- ✅ Quote and counter-quote — pass/fail examples side by side.
- ✅ Use `✅` / `❌` (and `🟥` / `🟧` / `🟨` / `⚪` where severity is meaningful) — these are semantic, not decorative.
- ❌ No hedging ("generally", "you might want to", "in most cases").
- ❌ No padding adjectives ("robust, scalable, modern").
- ❌ Don't address the user in second person inside `SKILL.md` — the reader is the AI agent; talk *about* the user in the third person.
- ❌ Don't write tutorial prose ("first, install dependencies"). Installation is in `manifest.json`.

## Skill categories (extend an existing one before proposing a new one)

The README groups skills into five categories. Prefer adding to one of these over inventing a new section:

1. **Pipeline glue** — skills that hand off to other skills (`brief-intake`, `doc-critique`).
2. **Dev workflow** — skills that act on code (`devils-advocate`).
3. **Diagrams** — visual artifacts (`architecture-diagrams`, `reverse-architecture`, `figma-diagrams`).
4. **Documentation** — written technical artifacts (`adr-generator`, `design-doc`, `runbook-generator`, `tech-comparison-matrix`).
5. **Stakeholder communication** — non-technical audiences (`audience-profile`, `slide-outliner`, `deck-builder`, `exec-summary`, `decision-log`).

A new section needs a use-case-first name, a one-sentence definition of what belongs in it, and at least one existing skill that would also fit there. Sections are cheap; ungrouped skills make the README harder to scan.

## Pointers

- Contributor & maintainer policy: [CONTRIBUTING.md](CONTRIBUTING.md)
- Voice & tone (most important section): [CONTRIBUTING.md → Voice & tone](CONTRIBUTING.md#voice--tone-the-most-important-section)
- Branching, PRs, and merge rules: [CONTRIBUTING.md → Branching, PRs, and merging](CONTRIBUTING.md#branching-prs-and-merging)
- Maintainer roster + bypass policy: [MAINTAINERS.md](MAINTAINERS.md)
- Repo overview & per-IDE install steps: [README.md](README.md)
- Claude Code project settings: [.claude/settings.json](.claude/settings.json) — currently empty
- Reference implementations for skill scripts: [`skills/deck-builder/scripts/`](skills/deck-builder/scripts/), [`skills/figma-diagrams/scripts/`](skills/figma-diagrams/scripts/)
