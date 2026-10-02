# AGENTS.md — Guidance for Autonomous Coding Agents

> Canonical guide for Copilot, Codex, Cursor, and other agentic IDEs operating on this repository.

## Repo in one paragraph

**skilldrop** is a collection of portable **Claude Skills** for the deliverables knowledge workers actually ship: diagrams, ADRs, design docs, runbooks, decks, decision logs, comparison matrices, exec summaries, structured critiques, and adversarial code review. Each skill is a plain directory at `packs/<pack>/skills/<name>/` containing a `SKILL.md` + `manifest.json` (+ optional `reference.md`, `templates/`, `lenses/`, `rubrics/`, `examples/`, `scripts/`, `requirements.txt`). Above the skills sit **loops** (`packs/<pack>/loops/<name>/LOOP.md` + `loop.json`, RFC-0028) — named sequences of stages over those skills with a gate between each, so the repo ships a way of operating and not only a bag of parts. A loop *sequences* skills; it never contains one. The pack a skill or loop sits in is its one home (RFC-0033, RFC-0034); each pack's metadata is `packs/<pack>/pack.json`, and `catalogue.json` holds pack order and outcomes. Installation is per-folder copy into the target IDE's skills/rules location — documented per-IDE install steps live in `README.md` (Claude Code, Cursor, Kiro, Continue, Cline, Aider).

## Golden rules

1. **Folder name = `SKILL.md` `name` = `manifest.json` `name`** (and for a loop: folder = `LOOP.md` `name` = `loop.json` `name`). Kebab-case, use-case-first, no version suffix. Changing any of the three without the others breaks slash-command invocation.
2. **Do not move** `packs/`, `LICENSE`, or `README.md`, and do not move a skill between packs without an RFC. A skill's path is `packs/<pack>/skills/<name>/`; moving it breaks every install instruction, GitHub link, and plugin that names that path (RFC-0034).
3. **Keep `SKILL.md` under ~500 lines.** Spill into `reference.md`, `templates/`, `lenses/`, `rubrics/`, or `examples/`. Agent context is the binding constraint — a bloated `SKILL.md` crowds out the user's actual prompt.
4. **Never invent commands, env vars, or file conventions.** Use those documented below. The only automated checks are `python3 validate.py` and `node bin/skilldrop.js validate`, run locally and by CI (`.github/workflows/release.yml`, which also publishes to npm on version bump — see **Releasing**). Don't pretend other test runners or linters exist.
5. **No secrets, no real customer names, no personal data** in templates, examples, or sample inputs. Placeholder data only.
6. **Voice is opinionated, not hedged.** Strip "generally", "consider", "you might want to". The `✅` / `❌` markers have semantic meaning — don't use them decoratively, don't add other decorative emoji.
7. **A skill never invokes a skill; a loop orders them.** Sequencing lives in `packs/<pack>/loops/<name>/loop.json` (RFC-0028) — that is what keeps a single-folder copy working in Cursor, Kiro, and Aider.
8. **Every new skill ships with `Quality bar` and `Anti-patterns to avoid` sections** — and so does every `LOOP.md`. A skill without them is a description, not a generator; a loop without them is a diagram. Both are enforced by `validate.py` (RFC-0016, RFC-0028).

## Verified commands (do not invent variants)

```bash
# Install a single skill into Claude Code — user-scope (every project)
mkdir -p ~/.claude/skills && cp -R packs/<pack>/skills/<skill-name> ~/.claude/skills/

# Install a single skill into Claude Code — project-scope (tracked with repo)
mkdir -p .claude/skills && cp -R packs/<pack>/skills/<skill-name> .claude/skills/

# Install Python deps for a skill that has them (currently figma-diagrams, deck-builder)
cd packs/<pack>/skills/<skill-name> && python3 -m pip install -r requirements.txt

# Consistency lint — run from the repo root before committing (works on Python 3.9+)
python3 validate.py

# Site build — NOTE: needs Python 3.12+ (PEP 701 f-strings). The macOS system python3 is
# 3.9 and raises a bare SyntaxError; use a Homebrew interpreter explicitly.
python3.14 build_site.py           # or any 3.12+
python3.14 build_site.py --check

# Loop diagrams — regenerate docs/loops/*.mmd and the README mermaid blocks from loop.json
python3 build_loops.py
python3 build_loops.py --check   # drift check; validate.py runs this for you

# llms.txt — the machine-readable index. Generated; validate.py fails on drift.
python3 build_llms.py
python3 build_llms.py --check

# CLI (npm package skilldrop-cli; from a clone use node bin/skilldrop.js)
node bin/skilldrop.js list | info <skill> | packs | agents | loops      # add --from <path|git-url[#ref]> for a third-party catalog
node bin/skilldrop.js install --agent <name...> [--project | --dest <dir>]   # subagents (RFC-0012); plain-copy targets only
node bin/skilldrop.js install --loop <name...> [--no-skills]     # loops + the stage skills they sequence (RFC-0028)
node bin/skilldrop.js install --loop --pack <name>               # every loop a pack declares
node bin/skilldrop.js uninstall --loop <name...>                 # removes the loop; stage skills stay
node bin/skilldrop.js install <skill...> [--pack <name>] [--all] [--with-related] [--from <src>] [--project | --local | --ide cursor|kiro|codex|antigravity|copilot | --dest <dir>]
node bin/skilldrop.js update | outdated | uninstall <skill...>   # same target flags; update follows each skill's recorded source
node bin/skilldrop.js install | update | uninstall ... --dry-run # print what would change, change nothing
node bin/skilldrop.js diff <skill> | doctor                      # installed copy vs catalog; ledger vs disk (report-only)
node bin/skilldrop.js new-skill <name> --pack <pack>             # scaffold a skill with every file validate.py checks
node bin/skilldrop.js validate [--from <src>]                    # structural check of a catalog (catalog authors)
node bin/skilldrop.js package <dir> [--pack a,b] [--skills x,y]  # vetted subset as a standalone catalogue + MIRROR.json
node bin/skilldrop.js init-catalogue <dir> [--pack <name>]       # start a private catalogue
node bin/skilldrop.js loop-stats [<file>] [--days N]             # summarise the opt-in loop run log (SKILLDROP_LOOP_LOG)

# Per-pack how-to + reference guides. Generated; validate.py fails on drift.
python3 build_pack_guides.py
python3 build_pack_guides.py --check

# Evals against a live model (needs ANTHROPIC_API_KEY; report-only, also weekly in CI)
python3 run_evals.py [--skills a,b] [--assertions]

# Benchmark: each eval with the skill and without it, with cost (RFC-0040). Paid; capped by --budget.
python3 run_bench.py --dry-run                                    # call count and rough cost; spends nothing
python3 run_bench.py [--skills a,b] [--models light,standard,heavy] [--trials N] [--budget USD]
python3 run_bench.py --backend claude-cli ...                     # agent runs through a signed-in Claude Code; no API key
python3 run_bench.py --backend claude-cli --publish docs/benchmarks/latest.json   # the summary the site renders
python3 run_bench.py --backend claude-cli --second-judge claude-opus-5-5         # a second blind judge, and how often the two agree

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

There is **no `make` target and no test command**. The automated checks are [`validate.py`](validate.py) — a stdlib-only consistency lint (name triple-match, tier sync with `model-routing.json`, `related`↔SKILL.md reference sync, description sync, pack membership, outcome membership (RFC-0026), evals shape, reference + link integrity and orphaned-material (RFC-0015), `Quality bar`/`Anti-patterns` sections + script dual-referencing + a heavy-tier `examples/` oracle (RFC-0016), and — for `agents/` — filename↔frontmatter `name` plus every `` `x` subagent `` a SKILL.md delegates to resolving to a real agent file) — and the CLI's structural check (`node bin/skilldrop.js validate`); both run locally before every commit and in CI on every push/PR ([`.github/workflows/release.yml`](.github/workflows/release.yml)). Everything beyond that is the manual-test pass documented in **Authoring a new skill** below: install the skill into a clean Claude Code session, run it end-to-end on a realistic input, and verify the output meets the skill's own quality bar.

## Releasing

The npm package (`skilldrop-cli`) releases automatically: bump `version` in [`package.json`](package.json), merge to `main`, and CI publishes via npm OIDC trusted publishing with provenance, then pushes a `v<version>` tag — version-gated, so a push without a bump publishes nothing (see [RFC-0004](docs/rfcs/0004-release-automation.md)). Bump the version whenever a skill change is worth shipping; users' `skilldrop outdated` only lights up on releases. The manual fallback (`npm publish` with the 2FA browser step) still works from the repo root.

Every version bump lands with a matching entry at the top of [`CHANGELOG.md`](CHANGELOG.md) — `## <version> — <YYYY-MM-DD>` plus one bullet per user-visible change, saying what a user can now do rather than which files moved. This is mechanically enforced from an unusual direction: `build_site.py` refuses to render the site when the changelog's newest version disagrees with `package.json`, so an undocumented release cannot deploy.

**Bump the third digit, one step at a time.** `0.9.0` → `0.9.1` → `0.9.2`. Never skip a number, and don't reach for a bigger bump because a release *feels* big. A **minor** release is a **third-digit** bump (`0.9.1` → `0.9.2`) — new skills, skill edits, pack changes, tier changes, docs, new CLI commands and flags, and bug fixes all ship this way. A **major** release is a **second-digit** bump (`0.9.x` → `0.10.0`) — a deliberate milestone the maintainer calls, not something a single feature triggers. `1.0.0` waits for an explicit stability commitment.

## File placement

| Kind | Where |
|---|---|
| New skill | `packs/<pack>/skills/<kebab-name>/SKILL.md` + `packs/<pack>/skills/<kebab-name>/manifest.json` |
| Long-form reference for a skill | `packs/<pack>/skills/<skill-name>/reference.md` |
| Paste-able starter content | `packs/<pack>/skills/<skill-name>/templates/<name>.md` |
| Worked example (input → output) | `packs/<pack>/skills/<skill-name>/examples/<name>.md` |
| Adversarial-sweep checklist (devils-advocate style) | `packs/<pack>/skills/<skill-name>/lenses/<name>.md` |
| Per-archetype quality bar (doc-critique style) | `packs/<pack>/skills/<skill-name>/rubrics/<archetype>.md` |
| Input files an eval's prompt names | `packs/<pack>/skills/<skill-name>/evals/files/<eval id>/` — copied into the working directory of a benchmark run (RFC-0040) |
| Acceptance checks for a skill | `packs/<pack>/skills/<skill-name>/evals/evals.json` (prompt + assertions) + `evals/eval_queries.json` (should/shouldn't-trigger phrases) |
| RFC for a new skill or structural change | `docs/rfcs/NNNN-<kebab-slug>.md` — copy [`docs/rfcs/0000-template.md`](docs/rfcs/0000-template.md), next sequential number |
| Long-form design doc (bigger than an RFC, not a skill) | `docs/designs/<name>.md` — e.g. the CLI command surface, the telemetry collection spec |
| Pack membership for a skill | The folder: put the skill at `packs/<pack>/skills/<name>/`, in exactly one pack. A skill every role needs goes in `core` (RFC-0033, RFC-0034) |
| Pack membership for a loop | The folder: `packs/<pack>/loops/<name>/`. That pack (or `core`) must hold every skill the loop's stages run; `validate.py` checks it |
| Pack metadata (description, `requires`, first-value) | `packs/<pack>/pack.json` (RFC-0032); a new pack also goes in `catalogue.json` `packs`, which sets display order |
| Outcome membership for a skill | `catalogue.json` `outcomes` — add the skill to at least one outcome (RFC-0026); packs say *who*, outcomes say *why* |
| User-visible change for a release | `CHANGELOG.md` — one bullet under `## <version> — <YYYY-MM-DD>`; the site reads the newest three and `build_site.py` refuses to build if the top version disagrees with `package.json` |
| Executable helper | `packs/<pack>/skills/<skill-name>/scripts/<name>.py` (or `.js`, `.sh`) |
| Python dep manifest for a skill | `packs/<pack>/skills/<skill-name>/requirements.txt` |
| New loop (a sequence over existing skills) | `packs/<pack>/loops/<kebab-name>/LOOP.md` + `loop.json` beside it — needs an RFC (RFC-0028) |
| Machine-readable index for models | Nothing to place by hand — `build_llms.py` generates `llms.txt` from the catalogue |
| Loop diagram | Nothing to place by hand — `build_loops.py` generates `docs/loops/<loop>.mmd` and the README's mermaid blocks from `loop.json`. Edit the contract, not the picture. |
| Machine-readable schema for a primitive | `contracts/<name>.schema.json` — closed schemas, checked by `validate.py`'s stdlib `check_schema()`. The shared gate verdict vocabulary is `contracts/terminals.json` |
| Long-form doc that would bloat the README | `guides/<kind>/<slug>.md` — frontmatter `title`/`summary`/`kind` (Diátaxis), and a link from `guides/README.md`. Both enforced (RFC-0029) |
| Claude Code project settings | `.claude/settings.json` — registers the repo as a local plugin marketplace for dogfooding; also holds hooks/permissions/env. Inert for non-Claude tools. |
| Per-pack Claude plugin output | Nothing to place by hand — `build_marketplace.py --dist` generates it and CI publishes it to the `plugins` branch. Putting a skill in a pack's folder is the whole edit (RFC-0027, RFC-0034). |

Anything outside `packs/`, `agents/`, and `contracts/` is repo policy or hygiene. System design lives in [ARCHITECTURE.md](ARCHITECTURE.md); long-form docs live in [guides/](guides/). New top-level directories should be proposed in a PR with rationale, not added silently.

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

**A skill with `scripts/` also declares `permissions`** (RFC-0039), so a reader and `skilldrop scan` can compare what the code does with what it says:

```json
"permissions": { "network": ["api.figma.com"], "commands": [], "files": "named-paths", "notes": "Reads FIGMA_TOKEN to call the Figma REST API." }
```

`network` lists the hosts the scripts contact (empty for none); `commands` the external programs they run (`"*"` for commands the user configures); `files` is `none`, `named-paths` (only paths the user passes), `project`, or `anywhere`. `validate.py` fails a script skill without the block, and `node bin/skilldrop.js validate` fails one whose scripts do something it doesn't declare. Declare what the code can do, not what it usually does.

`related` is the flat list of sibling skills this skill's `SKILL.md` references — hand-off targets, upstream feeders, and named alternatives alike (direction lives in the SKILL.md prose, not here). It exists so installers and users can grab a skill's companions in one pass. `validate.py` enforces the sync in both directions: every backticked sibling reference in `SKILL.md` must appear in `related`, and every `related` entry must be a real skill folder that `SKILL.md` actually references.

`handoff` is the **directed** companion to `related`, which is undirected and not a DAG
(RFC-0028). Each entry is a closed object — `{ to, when, purpose, fallback }`, all four
required:

```json
"handoff": [{
  "to": "nfr-spec",
  "when": "the functional requirements are agreed",
  "purpose": "Set the quality targets the design will be judged against.",
  "fallback": "If nfr-spec is absent, state latency, availability and scale targets inline as numbers, not adjectives."
}]
```

`fallback` is the field doing the real work: it makes **Sibling hand-offs are advisory**
(below) machine-readable rather than prose an agent may ignore, so a hand-off to a skill the
target environment lacks degrades in a stated way instead of dead-ending. Every `to` must
also appear in `related`, so the directed edge cannot drift from the enforced undirected one.
`validate.py` checks all of this, plus no self-hand-off and no duplicate target.

`hooks` is optional and only for loop-shaped skills that benefit from event automation (RFC-0006) — artifact generators carry none. Each entry is `{ event, action, description }`: `event` is one of `session-start`, `pre-commit-review`, `on-demand`; `action` is a real skill folder the hook points at; `description` is a short human line. The CLI wires these only under `--with-hooks`, projecting per install target and degrading where a target has no mechanism. `validate.py` checks the event vocabulary and that `action` resolves to a skill.

The `model` block is the colocated cost-routing hint — an **abstract, provider-neutral tier** (`light` / `standard` / `heavy`), never a vendor model name. It travels with the skill when copied into another IDE, and must match the skill's entry in the repo-root [`model-routing.json`](model-routing.json). See **Model routing** below.

## Anatomy of a skill

Every skill folder follows the same layout, so installation is identical everywhere:

```
packs/<pack>/skills/<skill-name>/
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

**3. Add supporting files as needed.** `templates/` = paste-able starting points; `reference.md` = long-form material that won't fit in `SKILL.md`; `lenses/<name>.md` = sweep checklists (devils-advocate); `rubrics/<archetype>.md` = per-archetype quality bars (doc-critique); `examples/<name>.md` = input → output for a non-obvious case. Reference **material** files (`reference.md`, `references/`, `lenses/`, `rubrics/`) from `SKILL.md` with a relative link — `validate.py` fails an orphaned one (RFC-0015). `examples/` are studied when present; linking them is encouraged but not required. A **heavy**-tier (adversarial/judgment) skill must ship at least one `examples/` input→output oracle (RFC-0016).

**4. Add `evals/` — the skill's acceptance checks.** Two small JSON files, no runner required. CI (`release.yml`) validates their *shape* via `validate.py`; the assertions themselves are executed by reading them during the manual test pass:

- `evals/evals.json` — `{ "skill_name": …, "evals": [ { "id", "prompt", "assertions": [ … ] } ] }`. At least one realistic prompt; assertions are the checkable statements a passing output satisfies (they should restate the skill's own `Quality bar` as verifiable claims about one concrete output).
- `evals/eval_queries.json` — `[ { "query": …, "should_trigger": true|false } ]`. 4+ phrases that should invoke the skill and 3+ near-misses that should route to a sibling skill instead. The `false` rows are the discipline: they force the `description` to draw a real boundary against sibling skills.

**Every skill ships evals** (full coverage since 0.13.8; `validate.py` fails a skill without both files). The `should_trigger: false` rows are where the care goes: each one is a real near-miss that belongs to a **named sibling**, taken from the skill's "When NOT to use" section and its `related` list — "help me present this" (`exec-summary` / `slide-outliner` / `deck-builder` / `audience-profile`), "define the contract" (`api-contract-draft` / `data-contract` / `db-schema-design`), "review this" (`devils-advocate` / `doc-critique` / `council-review` / `sonar-review`). Don't invent a collision to fill the file: a no-trigger row nobody would actually type documents nothing. Assertions come from the skill's own Quality bar, and every skill that handles facts gets a "does not invent X not in the prompt" assertion. The weekly [evals workflow](.github/workflows/evals.yml) runs the trigger queries against a live model and reports the results.

**5. Update the skill catalogue.** Add a row to [`guides/reference/skill-catalogue.md`](guides/reference/skill-catalogue.md) (under the right category), and to **Installing dependencies** in [`guides/how-to/install-per-ide.md`](guides/how-to/install-per-ide.md) if the skill has runtime deps.

**6. Test it manually.** Install into a clean Claude Code session (`cp -R packs/<pack>/skills/<name> ~/.claude/skills/`), then run the `evals/evals.json` prompt and check each assertion against the output; spot-check a `should_trigger: false` query routes elsewhere. Also verify: the agent finds `SKILL.md` without confusion; templates/lenses/rubrics are read at the right moment; scripts work from both `${CLAUDE_SKILL_DIR}/scripts/…` *and* a plain relative path. If you can, run it in a second IDE to catch portability issues.

## Authoring a new loop

A loop is a **sequence over skills that already exist**. Write one when the order and the
gates between existing skills are the thing worth shipping; write a skill when a new artifact
is. A loop that would need a skill nobody has written yet is blocked on that skill, not on
this section.

1. **RFC first**, same as a new skill — loops are a primitive and its membership is a
   structural decision (RFC-0028).
2. **`loop.json`** — `name`, `description` (use-case-first, trigger phrases at the end),
   `entrypoint: "LOOP.md"`, `kind` (`loop` or `wrapper`), `cap` (default 3), and `stages`.
   The contract is **closed**: an unknown key is a failure, not a no-op.
3. **Stages** carry `id`, `type` (`generate` / `verify` / `gate` — the three
   `agent-loop-design` mandates), `intent`, and `skills` (real folder names; `*` means any
   generator and is legal only in a `wrapper`).
4. **Gates** carry a repo-unique `id` (`G2`, `G2.1`), a `kind` (`mechanical` needs a real
   `script`; `review` and `human` must not have one), the `verdicts` they can emit, and
   `revise_to` naming an **earlier** stage. Every verdict must exist in
   [`contracts/terminals.json`](contracts/terminals.json) — a gate may not invent a new word
   for an outcome that already has one. Every gate needs at least one pass-class verdict, at
   least one non-pass, and must be able to emit `BLOCKED`.
5. **`LOOP.md`** — frontmatter `name` + `description` matching `loop.json` exactly, the stage
   table, how to run it, and the same `Quality bar` + `Anti-patterns to avoid` sections a
   skill ships. Include the degradation line: what to do when a stage's skill isn't installed,
   and the `## Run log (opt-in)` section copied from an existing loop (RFC-0038).
6. **No model tier.** A loop sequences skills and makes no model call of its own, so it has no
   entry in `model-routing.json`; `validate.py` fails one that does, by name.
7. **A loop's name may not collide with a skill's.** On install, `LOOP.md` projects to
   `<dest>/<name>/SKILL.md` — Claude Code and the other targets have no loop primitive, and
   `LOOP.md`'s frontmatter is already `SKILL.md`'s shape, so the two share one namespace.
8. **Put it in a pack** — the folder is `packs/<pack>/loops/<name>/` — and re-run `python3 build_loops.py`.

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
- **Declare `permissions`** in `manifest.json`: hosts contacted, external programs run, and where files are written (RFC-0039).
- **Read inputs from a file-path argument or stdin**, not a hard-coded Claude Code variable — the script should run as a standalone CLI.
- **Write outputs to a user-specified path**, not a hard-coded location.
- **Don't shell out to interactive commands** (`gh auth login`, `aws configure`) — those need the user; the skill shouldn't drive them.

See `packs/design/skills/deck-builder/scripts/build_deck.py` for the reference pattern.

## Before you commit

- [ ] PR is from a **feature branch**, not from `main`.
- [ ] **RFC exists and is `accepted`** for a new skill or structural change (`docs/rfcs/NNNN-*.md`); mark it `implemented` in the same PR.
- [ ] Folder name = `SKILL.md` `name` = `manifest.json` `name`.
- [ ] `SKILL.md` is **≤ ~500 lines** — long material moved into siblings.
- [ ] `Quality bar` and `Anti-patterns to avoid` sections are present.
- [ ] **`evals/` present**: `evals.json` with ≥1 prompt + assertions, `eval_queries.json` with trigger *and* no-trigger queries, the no-trigger rows naming real siblings. `validate.py` enforces presence and shape; whether the queries are realistic is your judgment.
- [ ] At least one **worked example** for new diagram, deck, or review skills.
- [ ] Description **leads with the use case** and **ends with trigger phrases**.
- [ ] Skill catalogue updated — a row in `guides/reference/skill-catalogue.md`, and in **Installing dependencies** (`guides/how-to/install-per-ide.md`) if the skill has runtime deps. The README is a short router (RFC-0035); only a new *pack* needs a README line.
- [ ] **Manual test pass** — installed the skill into a clean Claude Code session and ran it on a realistic input. Output meets the skill's own quality bar.
- [ ] Scripts (if any) reference both `${CLAUDE_SKILL_DIR}/scripts/…` **and** a plain relative `scripts/…` so non-Claude IDEs can find them.
- [ ] No secrets, no real customer data — placeholder values only.
- [ ] Voice matches the established opinionated tone (see below).
- [ ] **Model tier set** — new skill has a `model` block in `manifest.json` AND a matching entry in `model-routing.json`. The two agree.
- [ ] **`related` synced** — every sibling skill referenced in `SKILL.md` is in the manifest's `related` list.
- [ ] **Non-interactive line present** if the skill has a hard-stop condition — a self-contained sentence saying which inputs degrade to `[assumption]` and which emit `BLOCKED: need <X>`.
- [ ] **Pack membership** — new skill created under exactly one `packs/<pack>/skills/`; a new loop under exactly one `packs/<pack>/loops/` (RFC-0033, RFC-0034).
- [ ] **Outcome membership** — new skill added to at least one entry in `catalogue.json` `outcomes` (RFC-0026).
- [ ] **`CHANGELOG.md` entry** if the version was bumped — the site build fails without one.
- [ ] **GitHub About updated** if the skill/pack/subagent counts changed — `gh repo edit --description "…"`. This is the one surface `validate.py` cannot see (it is stdlib-only and off-repo), so it is the one that goes stale: it sat at `62 skills … 7 packs` for a while after the catalogue was 56 and 6. It is also what shows in search results and on the repo card, so it is the first thing a stranger reads.
- [ ] **Loop (if any) is complete** — `loop.json` validates against the closed contract, every named skill exists, gate ids are repo-unique, every verdict is in `contracts/terminals.json`, and `LOOP.md` carries `Quality bar` + `Anti-patterns to avoid`.
- [ ] **No loop in `model-routing.json`** — loops carry no tier.
- [ ] **`handoff` (if present) is complete** — every entry has `to`/`when`/`purpose`/`fallback`, and every `to` is also in `related`.
- [ ] **`python3 build_llms.py` run** if skills, loops, packs, contracts or guides changed — `llms.txt` is generated and drift fails the lint.
- [ ] **`python3 build_loops.py` run** if any `loop.json` changed — `docs/loops/*.mmd` and the README blocks are generated, and `validate.py` fails on drift.
- [ ] **Contracts satisfied** — the manifest / `loop.json` / agent frontmatter / guide frontmatter validates against its schema in `contracts/`. These are closed: a typo'd key fails.
- [ ] **New long-form doc is a guide**, not a README section — `guides/<kind>/<slug>.md` with Diátaxis frontmatter and a link from `guides/README.md`.
- [ ] **`python3 validate.py` passes** with no failures.

Of these, **`validate.py` (+ `node bin/skilldrop.js validate`) mechanically enforces**: every `contracts/` schema (manifests, `pack.json`, `catalogue.json`, loops, agent and guide frontmatter — all closed), the name triple (for skills *and* loops), the whole loop contract above, the ≤500-line warning, `Quality bar` + `Anti-patterns` sections, evals presence + shape, model-tier sync, `related` sync, pack membership, reference + link integrity, script dual-referencing, and a heavy-tier `examples/` oracle. The rest — the RFC existing, voice, the manual test pass, no-secrets / no-real-data, description discipline, the non-interactive line, the README update, and the GitHub About — are **human judgment**; a green lint does not vouch for them. Keep this split honest: if a rule becomes mechanically checkable, move it into `validate.py` rather than leaving it as a checklist claim.

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
7. **Agent engineering** — designing agentic systems themselves (`agent-loop-design`, `subagent-design`, `agent-budget`, `agent-threat-model`, `agents-md-generator`).
8. **AI adoption & observability** — measuring and gating AI usage itself (`ai-usage-report`, `llm-eval-harness`).
9. **Stakeholder communication** — non-technical audiences (`audience-profile`, `slide-outliner`, `deck-builder`, `exec-summary`, `decision-log`, `incident-comms`).

A new section needs a use-case-first name, a one-sentence definition of what belongs in it, and at least one existing skill that would also fit there. Sections are cheap; ungrouped skills make the README harder to scan.

## Skill packs

Categories say what a skill *is*; packs say *who needs it*. [`packs/`](packs/) holds `core` plus role-based packs (`solution-architect`, `product-manager`, `dev-team`, `sre-oncall`, `stakeholder-comms`, `design`, `ai-engineering`, `api-builder`), each installed in one command via the CLI or [`pack.py`](pack.py). Rules — rationale in [RFC-0001](docs/rfcs/0001-skill-packs.md), [RFC-0033](docs/rfcs/0033-core-pack-and-single-home-skills.md) and [RFC-0034](docs/rfcs/0034-physical-pack-layout.md):

- **A pack is a folder.** `packs/<pack>/skills/<name>/` is where a skill lives, and that path is the membership — there is no separate list to keep in sync. `packs/<pack>/pack.json` holds the pack's metadata.
- **One home per skill** (RFC-0033). A skill that serves every role, like `brief-intake`, goes in `core`, which each role pack `requires` and every installer brings along. Otherwise pick the role that produces the artifact. Every installer — the CLI, `pack.py`, the Claude plugins — brings `core` with a role pack.
- **Every skill belongs to exactly one pack.** A skill with no audience shouldn't have passed the RFC. The folder layout makes this structural; `validate.py` checks that no name has a folder in two packs, that every pack folder has a `pack.json` and is listed in `catalogue.json`, and that a pack holds every skill its loops run.
- **Every skill belongs to at least one outcome.** `catalogue.json` carries the second axis, `outcomes` (RFC-0026) — the README's nine categories restated as seven outcomes and made machine-readable, so the catalogue site can offer a *why am I here* axis beside the *who am I* one. Outcomes are a browse aid, never an install unit; the CLI does not take `--outcome`. `validate.py` applies the same two-way check packs get.

## Model routing

The repo ships a **cost-aware, provider-neutral model-selection layer**: each skill has an abstract tier (`light` / `standard` / `heavy`) describing how much reasoning the task needs, and a `providers` map resolves that tier to a concrete model for whatever tool the user runs (Claude Code, Cursor, Codex, Kiro, …). The premise — *the right tier for a skill is stable*, so the tier is decided **once per skill** and stored, never re-derived by an LLM per call (that would cost tokens to answer a fixed question). Pieces:

- [`model-routing.json`](model-routing.json) — **source of truth.** Per-skill tier + rationale, the `providers` tier→model map, `active_provider`, and mechanical escalation rules (large input, ambiguity, user override, never-downgrade-heavy).
- [`route.py`](route.py) — **pure-rules engine.** No API key, no network, instant. Keyword + length signals with small, transparent weights you tune at the top of the file. Resolves tier + concrete model from `model-routing.json`. Usable from any tool, CI, or a git hook (`python3 route.py --skill <name> --input <file>`).
- [`MODEL-ROUTING.md`](MODEL-ROUTING.md) — human-readable view + how to point it at a non-Claude tool.
- [`.claude/agents/model-router.md`](.claude/agents/model-router.md) — the **Claude Code implementation** of the spec (a dispatcher pinned to the lightest model) that runs `route.py`, resolves the active provider's model, and runs a skill on a subagent at that model. Other tools call the same `route.py` or consult the table directly.

Tier rule of thumb: **light** = mechanical mapping/extraction; **standard** = most generation (the default); **heavy** = adversarial reasoning / weighted judgment, never downgraded — and ships an `examples/` input→output oracle so the judgment has a behavioral contract, not just a structural one (`validate.py` enforces it, RFC-0016). Tiers are abstract — **never put a vendor model name in a skill's `model.tier`**; the provider map is the only place concrete models live.

When you add or change a skill, set its tier in **both** `model-routing.json` and the skill's `manifest.json` `model` block — they must agree (`light`/`standard`/`heavy`). `python3 validate.py` checks the two against each other.

## Pointers

- Human-facing contributor entry point (lanes, gates, release): [CONTRIBUTING.md](CONTRIBUTING.md) — a router over this file, which stays the source of truth
- Repo overview & per-IDE install steps: [README.md](README.md)
- RFCs (template + decisions): [docs/rfcs/](docs/rfcs/)
- Skill packs and outcomes: [packs/](packs/) + [catalogue.json](catalogue.json) + [catalog.py](catalog.py) (the one loader every script uses) + [pack.py](pack.py)
- Release history: [CHANGELOG.md](CHANGELOG.md)
- CLI (npm `skilldrop-cli`): [bin/skilldrop.js](bin/skilldrop.js) + [package.json](package.json) — copies skills verbatim, never transforms them; the npm `files` list must keep `packs/`, `catalogue.json`, `model-routing.json`
- Claude Code plugins: [build_marketplace.py](build_marketplace.py) — writes the committed `.claude-plugin/` on main, and (`--dist`) the per-pack plugin tree CI force-pushes to the generated `plugins` branch ([RFC-0027](docs/rfcs/0027-retire-agentbundle-export.md))
- Loops (the sequencing primitive): `packs/<pack>/loops/` + [RFC-0028](docs/rfcs/0028-loops-as-a-primitive.md)
- Loop diagram generator: [build_loops.py](build_loops.py) → [docs/loops/](docs/loops/)
- Machine-readable index: [build_llms.py](build_llms.py) → [llms.txt](llms.txt) (RFC-0030)
- System design and the enforcement model: [ARCHITECTURE.md](ARCHITECTURE.md)
- Long-form docs (Diátaxis): [guides/](guides/) — index at [guides/README.md](guides/README.md)
- Machine-readable contracts: [contracts/loop.schema.json](contracts/loop.schema.json), [contracts/terminals.json](contracts/terminals.json)
- Model routing: [MODEL-ROUTING.md](MODEL-ROUTING.md) + [model-routing.json](model-routing.json)
- Claude Code project settings: [.claude/settings.json](.claude/settings.json) — registers the repo as a local plugin marketplace (`skilldrop@skilldrop-local`) so the catalogue can be dogfooded from the working tree
- Reference implementations for skill scripts: [`packs/design/skills/deck-builder/scripts/`](packs/design/skills/deck-builder/scripts/), [`packs/solution-architect/skills/figma-diagrams/scripts/`](packs/solution-architect/skills/figma-diagrams/scripts/)
