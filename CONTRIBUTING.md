# Contributing to skilldrop

skilldrop has one primitive: **a skill** — a plain folder under `skills/` that any agentic IDE can install by copying it. Two supporting surfaces exist to make skills findable and installable: [`packs.json`](packs.json) (role bundles) and the `skilldrop-cli` npm package ([`bin/skilldrop.js`](bin/skilldrop.js)). Contributions come in three shapes, one per lane below.

## Before you start

Two reads, in order:

1. **[AGENTS.md](AGENTS.md)** — the source of truth. Golden rules, verified commands, file placement, skill anatomy, the pre-commit checklist, and the voice rules. This file routes you to it; it does not replace it.
2. **[README.md](README.md)** — what each skill does and how it installs into each IDE.

No setup step. The checks are stdlib Python and Node — `python3` and `node` are the only prerequisites, and only if you want to run the linters locally (CI runs them either way).

**Write an RFC first** if you are adding a new skill, a new top-level file or directory, changing the skill anatomy or manifest schema, or introducing a repo-wide convention. Copy [`docs/rfcs/0000-template.md`](docs/rfcs/0000-template.md) to `docs/rfcs/NNNN-<kebab-slug>.md` with the next sequential number. Keep it under a page — the RFC records the decision, the PR does the work. **No RFC needed** for fixes and improvements to an existing skill, doc corrections, or eval additions.

## The invariant this repo protects

**Skills are flat folders. Packs are metadata. The name matches in three places.**

skilldrop's entire premise is copy-install portability: `cp -R skills/<name> ~/.claude/skills/` has to work, in every IDE, forever. Three rules fall out of that, and they are the ones a well-meaning PR most often breaks:

- **Skills never move out of `skills/<kebab-name>/`.** No `packs/<pack>/<skill>/` nesting, no per-IDE projection directories, no build step that generates a skill from an upstream. What is in the tree is what gets copied. A pack is a named list in `packs.json` and nothing more ([RFC-0001](docs/rfcs/0001-skill-packs.md) records why physical packs were rejected).
- **Folder name = `SKILL.md` `name` = `manifest.json` `name`.** Kebab-case, use-case-first, no version suffix. Change one without the others and slash-command invocation breaks. `validate.py` fails the build on this.
- **`skills/`, `README.md`, and `LICENSE` do not move.** Every install instruction in the README is a hard-coded path.

## The three lanes

### 1. Adding a new skill

1. **RFC first** — `docs/rfcs/NNNN-<slug>.md`, including the four-part fit check (concrete artifact / portable / opinionated / category). A skill that is a generic chat helper with no artifact, a thin wrapper around one CLI command, or a duplicate of an existing skill does not belong here — improve the existing one instead.
2. **Create the folder** — `skills/<your-skill>/SKILL.md` + `manifest.json`, per the frontmatter and manifest shapes in [AGENTS.md](AGENTS.md#skillmd-frontmatter-required-exactly-this-shape). Keep `SKILL.md` under ~500 lines; spill into `reference.md`, `templates/`, `examples/`, `lenses/`, or `rubrics/`.
3. **Ship `Quality bar` and `Anti-patterns to avoid` sections.** A skill without them is a description, not a generator.
4. **Add `evals/`** — `evals.json` (≥1 realistic prompt + assertions) and `eval_queries.json` (phrases that should *and* should not trigger the skill). The no-trigger list is what keeps the `description` honest.
5. **Set the model tier in both places** — the `model` block in `manifest.json` and the skill's entry in [`model-routing.json`](model-routing.json). Tiers are abstract (`light` / `standard` / `heavy`); a vendor model name in a skill is always wrong. See [MODEL-ROUTING.md](MODEL-ROUTING.md).
6. **Declare an audience** — add the skill to at least one pack in [`packs.json`](packs.json). A skill with no audience should not have passed the RFC.
7. **Update `README.md`** — a row in **Skills in this repo** under an existing category, and a row in **Installing dependencies** if it has runtime deps.
8. **Match the voice.** Opinionated, not hedged; decisions, not options; ≤2 clarifying questions; `✅`/`❌` are semantic, never decorative. The full rules are in [AGENTS.md](AGENTS.md#voice--tone-non-negotiable) — re-read them before drafting.

### 2. Changing an existing skill

No RFC. The bar is that the skill stays internally consistent, because `validate.py` checks four kinds of drift:

- **Description sync** — `SKILL.md` frontmatter and `manifest.json` must carry the same string.
- **`related` sync, both directions** — every backticked sibling skill mentioned in `SKILL.md` must appear in the manifest's `related` list, and every `related` entry must be a real skill folder that `SKILL.md` actually references.
- **Tier sync** — `manifest.json` `model.tier` must equal the skill's tier in `model-routing.json`.
- **Pack membership** — the skill still belongs to a pack in `packs.json`.

If the change alters *what the skill produces*, redo the manual test pass (lane 3's gates, below) and update `evals/` to match. If it changes the trigger surface, update `eval_queries.json`.

### 3. Changing repo machinery

The CLI (`bin/skilldrop.js`), the installers (`pack.py`), routing (`route.py`, `model-routing.json`), hooks ([RFC-0006](docs/rfcs/0006-per-ide-hooks.md)), or `validate.py` itself. RFC required for anything that changes a convention or adds a top-level file; not for a bug fix.

Two things to keep true:

- **The CLI copies skills verbatim and never transforms them.** The moment it rewrites a skill on the way in, a skill installed by the CLI stops being identical to one installed by `cp -R`, and portability is gone.
- **`package.json` `files` must keep `bin/`, `skills/`, `packs.json`, and `model-routing.json`.** Dropping one ships a CLI that cannot find its catalog.

If you add a new invariant, teach `validate.py` to enforce it. A rule that only lives in prose is a rule that drifts.

## Before you open the PR

```bash
python3 validate.py                 # repo consistency lint (stdlib only)
node bin/skilldrop.js validate      # catalog structural check
```

Both run in CI on every push and PR ([`.github/workflows/release.yml`](.github/workflows/release.yml)). There is no `make` target and no test runner — do not add references to one.

Then:

- **Manual test pass.** Install the skill into a clean Claude Code session and run it end-to-end on a realistic input. The output has to clear the skill's own quality bar. This is the check the linters cannot do, and it is not optional for a new or substantially changed skill.
- **Work the full checklist** in [AGENTS.md → Before you commit](AGENTS.md#before-you-commit). It is the authoritative list; the lanes above are a summary of it.
- **Branch, don't push to `main`:**
  ```bash
  git checkout -b feat/<short-kebab-name>      # or fix/… docs/… chore/…
  git push origin feat/<short-kebab-name>
  gh pr create --base main --head <handle>:feat/<short-kebab-name>
  ```
- **Commit messages** are lowercase imperative, one line, naming the RFC when one applies — e.g. `add third-party catalogs to skilldrop-cli (RFC-0003)`. Not Conventional Commits.
- **Flip the RFC status to `implemented`** in the same PR that ships it, and fill in its **Decision** section.
- Every PR requires review from the repo owner ([`.github/CODEOWNERS`](.github/CODEOWNERS)).

## Cutting a release

The npm package `skilldrop-cli` publishes itself. Bump `version` in [`package.json`](package.json) and merge to `main` — CI publishes via npm OIDC trusted publishing with provenance, then pushes a `v<version>` tag. The job is version-gated: a push without a bump publishes nothing and fails nothing. Rationale in [RFC-0004](docs/rfcs/0004-release-automation.md).

Bump whenever a skill change is worth shipping — users' `skilldrop outdated` only lights up on a release, so unreleased skill improvements are invisible to everyone who installed via the CLI. The manual fallback (`npm publish` from the repo root, with the 2FA browser step) still works if CI is down.

**Increment the patch digit, one step at a time:** `0.4.0` → `0.4.1` → `0.4.2`. Never skip a number, and don't jump to a minor because the release *feels* significant.

| Bump | When |
|---|---|
| **Patch** (`0.4.1`) — the default | New skills, skill edits, pack changes, tier changes, docs, CLI bug fixes. Almost everything. |
| **Minor** (`0.5.0`) | The CLI's public surface changed: a new command, a new flag, or a changed default. |
| **Major** (`1.0.0`) | A deliberate stability commitment. Not yet. |

A docs-only change that ships nothing in `package.json` `files` (`bin/`, `skills/`, `packs.json`, `model-routing.json`) needs no bump at all — there is nothing new for the registry to carry.

## Where to find authoritative information

| Question | File |
|---|---|
| Rules, file placement, checklist, voice | [AGENTS.md](AGENTS.md) |
| Claude-Code-specific ergonomics (dogfooding, `${CLAUDE_SKILL_DIR}`) | [CLAUDE.md](CLAUDE.md) |
| What each skill does, per-IDE install steps | [README.md](README.md) |
| Why a structural decision was made | [docs/rfcs/](docs/rfcs/) |
| Long-form design (CLI surface, telemetry spec) | [docs/designs/](docs/designs/) |
| Which skills a role gets | [packs.json](packs.json) |
| What model tier a skill runs at, and why | [model-routing.json](model-routing.json) + [MODEL-ROUTING.md](MODEL-ROUTING.md) |
| What CI actually runs | [.github/workflows/release.yml](.github/workflows/release.yml) |

## When this file is wrong

Flag the drift in your PR instead of working around it. `AGENTS.md` wins any disagreement — this file is a router over it, and a router that points somewhere stale is a bug. Correcting it is a docs fix and needs no RFC; changing the process it describes needs one.

## License

MIT ([LICENSE](LICENSE)). Opening a PR means you agree your contribution ships under it.
