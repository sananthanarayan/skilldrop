# AGENTS.md — Guidance for Autonomous Coding Agents

> Canonical guide for Copilot, Codex, Cursor, and other agentic IDEs operating on this repository.

## Repo in one paragraph

**skilldrop** is a collection of portable **Claude Skills** for the deliverables knowledge workers actually ship: diagrams, ADRs, design docs, runbooks, decks, decision logs, comparison matrices, exec summaries, structured critiques, and adversarial code review. Each skill is a plain directory under `skills/` containing a `SKILL.md` + `manifest.json` (+ optional `reference.md`, `templates/`, `lenses/`, `rubrics/`, `examples/`, `scripts/`, `requirements.txt`). Installation is per-folder copy into the target IDE's skills/rules location — documented per-IDE install steps live in `README.md` (Claude Code, Cursor, Kiro, Continue, Cline, Aider).

## Golden rules

1. **Folder name = `SKILL.md` `name` = `manifest.json` `name`.** Kebab-case, use-case-first, no version suffix. Changing any of the three without the others breaks slash-command invocation.
2. **Do not move** `skills/`, `LICENSE`, or `README.md`. Skills are discovered by path; moving the directory breaks every install instruction the README documents.
3. **Keep `SKILL.md` under ~500 lines.** Spill into `reference.md`, `templates/`, `lenses/`, `rubrics/`, or `examples/`. Agent context is the binding constraint — a bloated `SKILL.md` crowds out the user's actual prompt.
4. **Never invent commands, env vars, or file conventions.** Use those documented below. This repo has no test runner, no CI, no linter at the root — don't pretend it does.
5. **No secrets, no real customer names, no personal data** in templates, examples, or sample inputs. Placeholder data only.
6. **Voice is opinionated, not hedged.** Strip "generally", "consider", "you might want to". The `✅` / `❌` markers have semantic meaning — don't use them decoratively, don't add other decorative emoji.
7. **Every new skill ships with `Quality bar` and `Anti-patterns to avoid` sections.** A skill without them is a description, not a generator. Both are enforced by the **Before you commit** checklist below.

## Verified commands (do not invent variants)

```bash
# Install a single skill into Claude Code — user-scope (every project)
mkdir -p ~/.claude/skills && cp -R skills/<skill-name> ~/.claude/skills/

# Install a single skill into Claude Code — project-scope (tracked with repo)
mkdir -p .claude/skills && cp -R skills/<skill-name> .claude/skills/

# Install Python deps for a skill that has them (currently figma-diagrams, deck-builder)
cd skills/<skill-name> && python3 -m pip install -r requirements.txt

# Branch + PR workflow
git checkout -b feat/<short-kebab-name>      # or fix/… docs/… chore/…
git push origin feat/<short-kebab-name>
gh pr create --base main --head <handle>:feat/<short-kebab-name>
```

There is **no `make` target, no test command, no lint command, no CI gate** at the repo root. Quality assurance is the manual-test pass documented in **Authoring a new skill** below: install the skill into a clean Claude Code session, run it end-to-end on a realistic input, and verify the output meets the skill's own quality bar.

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

## Anatomy of a skill

Every skill folder follows the same layout, so installation is identical everywhere:

```
skills/<skill-name>/
├── SKILL.md              # Instructions the agent reads — entry point
├── manifest.json         # Name, description, version, deps, required env vars
├── requirements.txt      # (optional) Python deps if the skill has scripts
├── reference.md          # (optional) Long-form reference material
├── examples/             # (optional) Worked examples the agent can study
├── templates/            # (optional) Starter snippets the agent copies from
├── lenses/               # (optional — devils-advocate style) Checklist files applied as a sweep
├── rubrics/              # (optional — doc-critique style) Per-archetype quality bars
└── scripts/              # (optional) Executable helpers the agent invokes
```

The folder name is the slug used for `/`-invocation: kebab-case, descriptive, use-case-first (`runbook-generator`, not `runbook-helper-v2`).

## Authoring a new skill

**1. Decide if it belongs here.** A skill belongs in skilldrop if its output is a *concrete artifact* (doc, diagram, deck, structured review, brief), it's *portable* (works in Claude Code and installs into Cursor / Kiro / Continue / Cline / Aider), it's *opinionated* (makes decisions instead of asking five questions), and it fits an existing category or justifies a new one. It does **not** belong if it's a generic chat helper with no artifact, depends on a proprietary internal service contributors can't reach, is a thin wrapper around one CLI command, or duplicates an existing skill — improve that one instead.

**2. Write `SKILL.md`.** Required frontmatter (shape above), then a body sectioned approximately like this — borrow from an existing skill to seed:

```markdown
# skill-name

{One- or two-sentence positioning: what it's for, how it relates to sibling skills.}

## How to respond
1. **{Imperative verb in bold.}** {The actual instruction.}
…

## Useful references in this skill
- [`reference.md`](reference.md) — {one line}

## Quality bar
- **{Rule.}** {Why, in one short sentence.}

## When to use this skill
- ✅ {Use case}

## When NOT to use this skill
- ❌ {Anti-use-case}

## Anti-patterns to avoid
- ❌ {Real mistake}
```

`Quality bar` and `Anti-patterns to avoid` are doing real work — they turn a "do this" skill into a "ships-good-output" skill. Don't skip them.

**3. Add supporting files as needed.** `templates/` = paste-able starting points; `reference.md` = long-form material that won't fit in `SKILL.md`; `lenses/<name>.md` = sweep checklists (devils-advocate); `rubrics/<archetype>.md` = per-archetype quality bars (doc-critique); `examples/<name>.md` = input → output for a non-obvious case. Always reference them from `SKILL.md` with a relative link.

**4. Update the README.** Add a row to the **Skills in this repo** table (under the right category), and to **Installing dependencies** if the skill has runtime deps.

**5. Test it manually.** Install into a clean Claude Code session (`cp -R skills/<name> ~/.claude/skills/`), then invoke it on a realistic input and verify: the agent finds `SKILL.md` without confusion; the output matches the `Quality bar`; templates/lenses/rubrics are read at the right moment; scripts work from both `${CLAUDE_SKILL_DIR}/scripts/…` *and* a plain relative path. If you can, run it in a second IDE to catch portability issues.

## Scripts must be portable

If a skill has executable scripts (Python, Node, shell):

- **Reference them with both `${CLAUDE_SKILL_DIR}/scripts/…` and a plain relative `scripts/…`** in `SKILL.md`. Claude Code sets `CLAUDE_SKILL_DIR`; other IDEs don't.
- **Pin dependencies** in `requirements.txt` (Python) or `package.json` (Node). Don't rely on a globally installed version.
- **Read inputs from a file-path argument or stdin**, not a hard-coded Claude Code variable — the script should run as a standalone CLI.
- **Write outputs to a user-specified path**, not a hard-coded location.
- **Don't shell out to interactive commands** (`gh auth login`, `aws configure`) — those need the user; the skill shouldn't drive them.

See `skills/deck-builder/scripts/build_deck.py` for the reference pattern.

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

skilldrop skills are **opinionated, not generic** — that's the difference between a useful skill and a noisy one. New skills must match the established voice. This is the most important section; re-read it before drafting any `SKILL.md` content.

### Do

- ✅ **Make decisions for the user.** "Default to MADR. Use Nygard only when the user explicitly asks for the classic format." Not "you could consider either, depending on preference." Pick defaults; cap clarifying questions at 2.
- ✅ **Use concrete examples, not abstract advice.** ❌ "Use clear titles." ✅ "Title is a noun phrase, not a verb phrase: ✅ *'Use Postgres as primary datastore'* — ❌ *'Decide what database to use'*."
- ✅ **Quote and counter-quote.** When showing a rule, put a passing and a failing example side by side.
- ✅ **Be specific about anti-patterns.** List the *real* mistakes you've seen, not theoretical ones.
- ✅ **Have a quality bar.** A skill without one is a description, not a generator. Every concrete output should be checkable against it.
- ✅ **Use the `✅` / `❌` markers** (and `🟥` / `🟧` / `🟨` / `⚪` where severity is meaningful) consistently — they're semantic, not decorative.
- ✅ **Lead with the rule, then the rationale.** "Title is a noun phrase, not a verb phrase. Why: …" — not "You should think about titles because…"

### Don't

- ❌ **Hedge.** "Generally", "consider", "you might want to", "in most cases" — strip them. If a rule has real exceptions, name them.
- ❌ **Write tutorials.** This is instructions to an AI agent, not documentation. Skip "first, install dependencies" prose — it's in `manifest.json`.
- ❌ **Pad with adjectives.** "Robust, scalable, modern, next-generation" are all noise.
- ❌ **Address the user in second person inside `SKILL.md`.** The reader is the AI agent; talk *about* the user in the third person.
- ❌ **Ask 4+ clarifying questions before producing output.** Cap at 2; pick defaults for everything else.
- ❌ **Use emojis decoratively.** Only the semantic markers above carry meaning.

### Description-field discipline

The `description` in frontmatter and `manifest.json` is the *most-read* string in your skill — agents match the user's prompt against it to decide whether to invoke. Two rules:

- **Lead with the use case, not the implementation.** ✅ "Generate an Architecture Decision Record from a context-decision-consequences brief." — ❌ "Markdown ADR generator using MADR format."
- **End with trigger phrases.** "Use whenever the user wants to capture an architectural decision, write an ADR, or document a 'we decided X because Y' moment." This is what the LLM matches against fuzzy prompts.

## Skill categories (extend an existing one before proposing a new one)

The README groups skills into five categories. Prefer adding to one of these over inventing a new section:

1. **Pipeline glue** — skills that hand off to other skills (`brief-intake`, `doc-critique`).
2. **Dev workflow** — skills that act on code (`devils-advocate`).
3. **Diagrams** — visual artifacts (`architecture-diagrams`, `reverse-architecture`, `figma-diagrams`).
4. **Documentation** — written technical artifacts (`adr-generator`, `design-doc`, `runbook-generator`, `tech-comparison-matrix`).
5. **Stakeholder communication** — non-technical audiences (`audience-profile`, `slide-outliner`, `deck-builder`, `exec-summary`, `decision-log`).

A new section needs a use-case-first name, a one-sentence definition of what belongs in it, and at least one existing skill that would also fit there. Sections are cheap; ungrouped skills make the README harder to scan.

## Pointers

- Repo overview & per-IDE install steps: [README.md](README.md)
- Claude Code project settings: [.claude/settings.json](.claude/settings.json) — currently empty
- Reference implementations for skill scripts: [`skills/deck-builder/scripts/`](skills/deck-builder/scripts/), [`skills/figma-diagrams/scripts/`](skills/figma-diagrams/scripts/)
