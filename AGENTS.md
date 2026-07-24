# AGENTS.md — Guidance for Autonomous Coding Agents

> Canonical guide for Copilot, Codex, Cursor, and other agentic IDEs operating on this repository.

## Repo in one paragraph

**skilldrop** is a collection of portable **Claude Skills** for the deliverables knowledge workers actually ship: diagrams, ADRs, design docs, runbooks, decks, decision logs, comparison matrices, exec summaries, structured critiques, and adversarial code review. Each skill is a plain directory under `skills/` containing a `SKILL.md` + `manifest.json` (+ optional `reference.md`, `templates/`, `lenses/`, `rubrics/`, `examples/`, `scripts/`, `requirements.txt`). Installation is per-folder copy into the target IDE's skills/rules location — documented per-IDE install steps live in `README.md` (Claude Code, Cursor, Kiro, Continue, Cline, Aider).

## Golden rules

1. **Folder name = `SKILL.md` `name` = `manifest.json` `name`.** Kebab-case, use-case-first, no version suffix. Changing any of the three without the others breaks slash-command invocation.
2. **Do not move** `skills/`, `LICENSE`, or `README.md`. Skills are discovered by path; moving the directory breaks every install instruction the README documents.
3. **Keep `SKILL.md` under ~500 lines.** Spill into `reference.md`, `templates/`, `lenses/`, `rubrics/`, or `examples/`. Agent context is the binding constraint — a bloated `SKILL.md` crowds out the user's actual prompt.
4. **Never invent commands, env vars, or file conventions.** Use those documented below. The only automated checks are `python3 validate.py` and `node bin/skilldrop.js validate`, run locally and by CI (`.github/workflows/release.yml`, which also publishes to npm on version bump — see **Releasing**). Don't pretend other test runners or linters exist.
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

# Consistency lint — run from the repo root before committing
python3 validate.py

# CLI (npm package skilldrop-cli; from a clone use node bin/skilldrop.js)
node bin/skilldrop.js list | info <skill> | packs                # add --from <path|git-url[#ref]> for a third-party catalog
node bin/skilldrop.js install <skill...> [--pack <name>] [--all] [--with-related] [--from <src>] [--project | --ide cursor|kiro | --dest <dir>]
node bin/skilldrop.js update | outdated | uninstall <skill...>   # same target flags; update follows each skill's recorded source
node bin/skilldrop.js validate [--from <src>]                    # structural check of a catalog (catalog authors)

# Skill packs — list packs / list a pack's skills / install a pack
python3 pack.py
python3 pack.py <pack-name>
python3 pack.py <pack-name> --install              # user scope (~/.claude/skills/)
python3 pack.py <pack-name> --install --project    # project scope (.claude/skills/)
python3 pack.py <pack-name> --install --dest <dir> # any dir (e.g. .cursor/skills)

# Branch + PR workflow
git checkout -b feat/<short-kebab-name>      # or fix/… docs/… chore/…
git push origin feat/<short-kebab-name>
gh pr create --base main --head <handle>:feat/<short-kebab-name>
```

There is **no `make` target and no test command**. The automated checks are [`validate.py`](validate.py) — a stdlib-only consistency lint (name triple-match, tier sync with `model-routing.json`, `related`↔SKILL.md reference sync, description sync, pack membership, evals shape) — and the CLI's structural check (`node bin/skilldrop.js validate`); both run locally before every commit and in CI on every push/PR ([`.github/workflows/release.yml`](.github/workflows/release.yml)). Everything beyond that is the manual-test pass documented in **Authoring a new skill** below:

## Releasing

The npm package (`skilldrop-cli`) releases automatically: bump `version` in [`package.json`](package.json), merge to `main`, and CI publishes via npm OIDC trusted publishing with provenance — version-gated, so a push without a bump publishes nothing (see [RFC-0004](docs/rfcs/0004-release-automation.md)). Bump the version whenever a skill change is worth shipping; users' `skilldrop outdated` only lights up on releases. The manual fallback (`npm publish` with the 2FA browser step) still works from the repo root. install the skill into a clean Claude Code session, run it end-to-end on a realistic input, and verify the output meets the skill's own quality bar.

## File placement

| Kind | Where |
|---|---|
| New skill | `skills/<kebab-name>/SKILL.md` + `skills/<kebab-name>/manifest.json` |
| Long-form reference for a skill | `skills/<skill-name>/reference.md` |
| Paste-able starter content | `skills/<skill-name>/templates/<name>.md` |
| Worked example (input → output) | `skills/<skill-name>/examples/<name>.md` |
| Adversarial-sweep checklist (devils-advocate style) | `skills/<skill-name>/lenses/<name>.md` |
| Per-archetype quality bar (doc-critique style) | `skills/<skill-name>/rubrics/<archetype>.md` |
| Acceptance checks for a skill | `skills/<skill-name>/evals/evals.json` (prompt + assertions) + `evals/eval_queries.json` (should/shouldn't-trigger phrases) |
| RFC for a new skill or structural change | `docs/rfcs/NNNN-<kebab-slug>.md` — copy [`docs/rfcs/0000-template.md`](docs/rfcs/0000-template.md), next sequential number |
| Long-form design doc (bigger than an RFC, not a skill) | `docs/designs/<name>.md` — e.g. the CLI command surface, the telemetry collection spec |
| Pack membership for a skill | `packs.json` — add the skill to at least one pack |
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
  "related": [],
  "tags": ["tag1", "tag2", "tag3"],
  "model": { "tier": "standard", "rationale": "One sentence — why this tier fits what the skill does." }
}
```

If the skill has no scripts, leave `deps` empty. `env.required` is for vars the skill cannot work without (e.g. `FIGMA_TOKEN` for `figma-diagrams`); `env.optional` is for vars that change behaviour but aren't blockers.

`related` is the flat list of sibling skills this skill's `SKILL.md` references — hand-off targets, upstream feeders, and named alternatives alike (direction lives in the SKILL.md prose, not here). It exists so installers and users can grab a skill's companions in one pass. `validate.py` enforces the sync in both directions: every backticked sibling reference in `SKILL.md` must appear in `related`, and every `related` entry must be a real skill folder that `SKILL.md` actually references.

The `model` block is the colocated cost-routing hint — an **abstract, provider-neutral tier** (`light` / `standard` / `heavy`), never a vendor model name. It travels with the skill when copied into another IDE, and must match the skill's entry in the repo-root [`model-routing.json`](model-routing.json). See **Model routing** below.

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
├── evals/                # (recommended for new skills) evals.json + eval_queries.json — see below
└── scripts/              # (optional) Executable helpers the agent invokes
```

The folder name is the slug used for `/`-invocation: kebab-case, descriptive, use-case-first (`runbook-generator`, not `runbook-helper-v2`).

## Authoring a new skill

**0. Write the RFC first.** New skills, new top-level files/directories, changes to the skill anatomy or manifest schema, and new repo-wide conventions all start as an RFC: copy [`docs/rfcs/0000-template.md`](docs/rfcs/0000-template.md) to `docs/rfcs/NNNN-<slug>.md` (next sequential number), fill in the problem, fit check, proposal, and alternatives — under a page — and mark it `accepted` before building, `implemented` when the PR merges. Fixes and improvements to an existing skill, doc corrections, and eval additions do **not** need one. The RFC is where step 1's fit decision gets recorded, so a rejected idea leaves a trace and doesn't get re-litigated.

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

**4. Add `evals/` — the skill's acceptance checks.** Two small JSON files, no runner required (this repo has no CI; they're executed by reading them during the manual test pass):

- `evals/evals.json` — `{ "skill_name": …, "evals": [ { "id", "prompt", "assertions": [ … ] } ] }`. At least one realistic prompt; assertions are the checkable statements a passing output satisfies (they should restate the skill's own `Quality bar` as verifiable claims about one concrete output).
- `evals/eval_queries.json` — `[ { "query": …, "should_trigger": true|false } ]`. 4+ phrases that should invoke the skill and 3+ near-misses that should route to a sibling skill instead. The `false` rows are the discipline: they force the `description` to draw a real boundary against sibling skills.

**5. Update the README.** Add a row to the **Skills in this repo** table (under the right category), and to **Installing dependencies** if the skill has runtime deps.

**6. Test it manually.** Install into a clean Claude Code session (`cp -R skills/<name> ~/.claude/skills/`), then run the `evals/evals.json` prompt and check each assertion against the output; spot-check a `should_trigger: false` query routes elsewhere. Also verify: the agent finds `SKILL.md` without confusion; templates/lenses/rubrics are read at the right moment; scripts work from both `${CLAUDE_SKILL_DIR}/scripts/…` *and* a plain relative path. If you can, run it in a second IDE to catch portability issues.

## Sibling hand-offs are advisory

Skills install à la carte — never assume a referenced sibling is present in the target environment. Two rules follow:

- **Authoring:** reference siblings freely (hand-offs, upstream feeders, "use X instead" alternatives) — the pipeline story is a feature. List every referenced sibling in the manifest's `related` block; `validate.py` enforces the sync.
- **Executing** (for any agent running an installed skill): a hand-off target that isn't installed degrades gracefully — name the missing skill and skilldrop as its source, then do the minimal inline version of what the hand-off would have done. A dangling hand-off is never an error and never a reason to stop.

## Non-interactive invocation

Skills cap clarifying questions at 2, and some hard-block on a missing anchor (a goal, a decision, a persona). In non-interactive contexts — a subagent dispatched by `model-router`, CI, a one-shot headless run — there is no user to ask. The convention:

- **Questions degrade to tagged assumptions.** Derive the most defensible answer from the input, tag it `[assumption]`, and state it at the top of the output as the first thing to confirm.
- **Blockers degrade to a structured `BLOCKED` output**, not a guess. When the missing anchor is one whose fabrication would corrupt the artifact (inventing the company's OKRs, the feature's goal, the customer), emit `BLOCKED: need <X>` naming exactly what's missing and what to rerun with — the same shape as `feature-implement-loop`'s `BLOCKED` status. A useful refusal beats a confident fabrication.
- **The rule must travel with the skill.** Each skill with a stop condition carries its own self-contained non-interactive line in `SKILL.md` — never a reference to this file, which doesn't get copied on install.

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
- [ ] **RFC exists and is `accepted`** for a new skill or structural change (`docs/rfcs/NNNN-*.md`); mark it `implemented` in the same PR.
- [ ] Folder name = `SKILL.md` `name` = `manifest.json` `name`.
- [ ] `SKILL.md` is **≤ ~500 lines** — long material moved into siblings.
- [ ] `Quality bar` and `Anti-patterns to avoid` sections are present.
- [ ] **`evals/` present** — `evals.json` with ≥1 prompt + assertions, `eval_queries.json` with trigger *and* no-trigger queries.
- [ ] At least one **worked example** for new diagram, deck, or review skills.
- [ ] Description **leads with the use case** and **ends with trigger phrases**.
- [ ] `README.md` updated — row added to **Skills in this repo**, and to **Installing dependencies** if the skill has runtime deps.
- [ ] **Manual test pass** — installed the skill into a clean Claude Code session and ran it on a realistic input. Output meets the skill's own quality bar.
- [ ] Scripts (if any) reference both `${CLAUDE_SKILL_DIR}/scripts/…` **and** a plain relative `scripts/…` so non-Claude IDEs can find them.
- [ ] No secrets, no real customer data — placeholder values only.
- [ ] Voice matches the established opinionated tone (see below).
- [ ] **Model tier set** — new skill has a `model` block in `manifest.json` AND a matching entry in `model-routing.json`. The two agree.
- [ ] **`related` synced** — every sibling skill referenced in `SKILL.md` is in the manifest's `related` list.
- [ ] **Non-interactive line present** if the skill has a hard-stop condition — a self-contained sentence saying which inputs degrade to `[assumption]` and which emit `BLOCKED: need <X>`.
- [ ] **Pack membership** — new skill added to at least one pack in `packs.json`.
- [ ] **`python3 validate.py` passes** with no failures.

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

The README groups skills into these categories. Prefer adding to one of them over inventing a new section:

1. **Pipeline glue** — skills that hand off to other skills (`brief-intake`, `doc-critique`).
2. **Product strategy** — direction-setting above any single feature (`prfaq`, `strategy-analysis`, `okr-cascade`).
3. **Planning & delivery** — SDLC steps around the code itself (`prd-draft`, `user-story-splitter`, `test-plan-generator`, `migration-plan`).
4. **Dev workflow** — skills that act on code (`devils-advocate`, `feature-implement-loop`, `council-review`).
5. **Diagrams** — visual artifacts (`architecture-diagrams`, `reverse-architecture`, `figma-diagrams`, `user-journey-map`).
6. **Documentation** — written technical artifacts (`adr-generator`, `design-doc`, `runbook-generator`, `tech-comparison-matrix`).
7. **Agent engineering** — designing agentic systems themselves (`agent-loop-design`, `subagent-design`, `agent-budget`).
8. **AI adoption & observability** — measuring and gating AI usage itself (`ai-usage-report`, `llm-eval-harness`).
9. **Stakeholder communication** — non-technical audiences (`audience-profile`, `slide-outliner`, `deck-builder`, `exec-summary`, `decision-log`, `incident-comms`).

A new section needs a use-case-first name, a one-sentence definition of what belongs in it, and at least one existing skill that would also fit there. Sections are cheap; ungrouped skills make the README harder to scan.

## Skill packs

Categories say what a skill *is*; packs say *who needs it*. [`packs.json`](packs.json) defines role-based bundles (`solution-architect`, `product-manager`, `dev-team`, `sre-oncall`, `stakeholder-comms`, `ai-engineering`) installed in one command via [`pack.py`](pack.py). Rules — rationale in [RFC-0001](docs/rfcs/0001-skill-packs.md):

- **Packs are metadata only.** Skills never move out of flat `skills/<name>` folders (golden rules 1–2); a pack is a named list, nothing more.
- **Packs may overlap** — `brief-intake` legitimately serves three roles. A skill listed in every pack is a smell (it means the packs aren't choosing).
- **Every skill belongs to at least one pack.** A skill with no audience shouldn't have passed the RFC. `validate.py` enforces both this and that every pack entry is a real skill folder.

## Model routing

The repo ships a **cost-aware, provider-neutral model-selection layer**: each skill has an abstract tier (`light` / `standard` / `heavy`) describing how much reasoning the task needs, and a `providers` map resolves that tier to a concrete model for whatever tool the user runs (Claude Code, Cursor, Codex, Kiro, …). The premise — *the right tier for a skill is stable*, so the tier is decided **once per skill** and stored, never re-derived by an LLM per call (that would cost tokens to answer a fixed question). Pieces:

- [`model-routing.json`](model-routing.json) — **source of truth.** Per-skill tier + rationale, the `providers` tier→model map, `active_provider`, and mechanical escalation rules (large input, ambiguity, user override, never-downgrade-heavy).
- [`route.py`](route.py) — **pure-rules engine.** No API key, no network, instant. Keyword + length signals with small, transparent weights you tune at the top of the file. Resolves tier + concrete model from `model-routing.json`. Usable from any tool, CI, or a git hook (`python3 route.py --skill <name> --input <file>`).
- [`MODEL-ROUTING.md`](MODEL-ROUTING.md) — human-readable view + how to point it at a non-Claude tool.
- [`.claude/agents/model-router.md`](.claude/agents/model-router.md) — the **Claude Code implementation** of the spec (a dispatcher pinned to the lightest model) that runs `route.py`, resolves the active provider's model, and runs a skill on a subagent at that model. Other tools call the same `route.py` or consult the table directly.

Tier rule of thumb: **light** = mechanical mapping/extraction; **standard** = most generation (the default); **heavy** = adversarial reasoning / weighted judgment, never downgraded. Tiers are abstract — **never put a vendor model name in a skill's `model.tier`**; the provider map is the only place concrete models live.

When you add or change a skill, set its tier in **both** `model-routing.json` and the skill's `manifest.json` `model` block — they must agree (`light`/`standard`/`heavy`). `python3 validate.py` checks the two against each other.

## Pointers

- Repo overview & per-IDE install steps: [README.md](README.md)
- RFCs (template + decisions): [docs/rfcs/](docs/rfcs/)
- Skill packs: [packs.json](packs.json) + [pack.py](pack.py)
- CLI (npm `skilldrop-cli`): [bin/skilldrop.js](bin/skilldrop.js) + [package.json](package.json) — copies skills verbatim, never transforms them; the npm `files` list must keep `skills/`, `packs.json`, `model-routing.json`
- Model routing: [MODEL-ROUTING.md](MODEL-ROUTING.md) + [model-routing.json](model-routing.json)
- Claude Code project settings: [.claude/settings.json](.claude/settings.json) — currently empty
- Reference implementations for skill scripts: [`skills/deck-builder/scripts/`](skills/deck-builder/scripts/), [`skills/figma-diagrams/scripts/`](skills/figma-diagrams/scripts/)
