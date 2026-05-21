# Contributing to skilldrop

Thanks for considering a contribution. skilldrop's value is in **opinionated, portable, drop-in skills** — most of these guidelines exist to keep new skills consistent with that promise.

Most of the time, contributing means one of these three things:

1. **Adding a new skill** — a new directory under `skills/` with the standard layout.
2. **Improving an existing skill** — tightening the rubric, adding a template, fixing a quality-bar gap, adding a worked example.
3. **Reporting a bug or proposing a skill** — open an issue with the use case.

This guide covers all three.

---

## Branching, PRs, and merging

This is the *one* hard rule in this repo. Everything else is taste; this is mechanics.

### The rule

> **Contributors:** all changes go through a pull request from a feature branch. No direct commits to `main`. Only a maintainer can approve and merge.
>
> **Maintainers:** the same workflow is the default — review each other's PRs, don't self-approve casual changes. But maintainers *may* bypass the PR flow and commit directly to `main` when the situation calls for it (see [Maintainer bypass](#maintainer-bypass-when-direct-commits-are-ok), below).

The maintainer list lives in [`MAINTAINERS.md`](MAINTAINERS.md).

### The workflow

```bash
# 1. Fork (if you're not a maintainer) and clone
git clone git@github.com:<your-handle>/skilldrop.git
cd skilldrop
git remote add upstream git@github.com:sanjay-ananth/skilldrop.git

# 2. Sync main, then branch from it
git checkout main
git pull upstream main
git checkout -b feat/<short-kebab-name>   # or fix/… or docs/… or chore/…

# 3. Make changes, commit
git add <files>
git commit -m "<concise, imperative subject line>"

# 4. Push your branch and open a PR
git push origin feat/<short-kebab-name>
gh pr create --base main --head <your-handle>:feat/<short-kebab-name>
```

### Branch naming

- `feat/<name>` — new skill or new feature in an existing skill.
- `fix/<name>` — bug fix.
- `docs/<name>` — README, CONTRIBUTING, MAINTAINERS, examples.
- `chore/<name>` — version bump, deps, repo hygiene.

The `<name>` part is short, kebab-case, descriptive — `feat/threat-model-skill`, `fix/runbook-rollback-command`, not `feat/sanjay-changes`.

### Pull-request expectations

- **From a feature branch, never from `main`.**
- **Branch is up to date with `main`** before review (rebase preferred for clean history; merge is also fine).
- **The repository's PR template is filled in** — including the worked example for new skills and the manual-test checkbox. The template auto-loads when you open the PR.
- **CODEOWNERS will auto-request review from a maintainer** — please don't add reviewers manually unless asked to.
- **CI / hooks (if any) must pass** before merge. A red CI gate is the maintainer's signal to wait.

### Who can do what

| Action | Contributor | Maintainer |
|---|---|---|
| Push to a feature branch | ✅ | ✅ |
| Open a PR | ✅ | ✅ |
| Review another contributor's PR | ✅ (review comments welcome) | ✅ (approval counts) |
| Approve a PR | ❌ | ✅ |
| Merge a PR | ❌ | ✅ |
| Push directly to `main` | ❌ | ✅ — discouraged, but allowed for the cases below |
| Force-push to a feature branch *you own* | ✅ | ✅ |
| Force-push to `main` | ❌ | ❌ — disabled at the protection layer for everyone |

### Maintainer bypass: when direct commits are OK

The default for maintainers is still: open a PR, request review from the other maintainer, merge after approval. The PR audit trail, the worked-example field, and the CODEOWNERS sign-off are how the project's quality bar stays calibrated — going through that flow even for your own changes is the right habit.

That said, there are legitimate cases for committing directly to `main`:

| Scenario | Why direct commit is fine |
|---|---|
| **Trivial repo hygiene** — typo in a comment, fixing a broken link, version bump after a merged PR | The change has no semantic content for an LLM to misinterpret or a contributor to misread. |
| **Urgent fix** — broken main, leaked secret, vulnerable dependency to patch in minutes | The cost of waiting for a second review exceeds the cost of bypassing it. |
| **Recovery from a bad merge** — reverting a PR that broke something | A PR-of-a-PR for an emergency revert is bureaucracy. |
| **Maintainer is the only one online** — solo + non-trivial change that can't wait | Document in the commit body why the bypass was used and what to verify post-hoc. |

When you bypass, the **commit message earns its keep**. The body should answer the questions a PR description would have:

```
chore: bump python-pptx to 0.7.0

Why: CVE-2024-XXXX in 0.6.x; production decks fail to render.
Verification: regenerated the worked example in deck-builder/examples/ — output matches.
Skipping PR: solo maintainer online, fix needed before EOD.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

When you bypass *casually* — for changes that don't fit the table above — you're spending the audit trail's value for a few minutes of saved time. Don't make a habit of it. If you find yourself bypassing for non-urgent skill changes, that's a signal the PR flow is too heavy and worth tightening, not a signal to keep bypassing.

### Recommended branch-protection settings (for maintainers setting this up on GitHub)

These enforce the rule above for contributors, while leaving the maintainer bypass intact for emergencies. Configure once at **Settings → Branches → Branch protection rules → Add rule** for `main`:

- ✅ **Require a pull request before merging**
  - ✅ Require approvals — `1`
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners
  - ✅ Restrict who can dismiss pull request reviews — maintainers only
- ✅ **Require status checks to pass before merging** (if/when CI exists)
- ✅ **Require branches to be up to date before merging**
- ✅ **Require conversation resolution before merging**
- ✅ **Require linear history** (avoids merge-commit clutter; choose squash or rebase merge in repo settings)
- ❌ **Do *not* enable "Include administrators"** — this is the setting that lets maintainers bypass when needed. Keeping it off means the PR/review rule is enforced for everyone *except* repo admins (i.e. the maintainers). Contributors still hit the rule.
- ✅ **Block force pushes** to `main`
- ✅ **Block deletions** of `main`

The equivalent `gh` command (run by a repo admin):

```bash
gh api -X PUT repos/sanjay-ananth/skilldrop/branches/main/protection \
  --input - <<'EOF'
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
```

The key field is `"enforce_admins": false` — that's what preserves the maintainer bypass. Flipping it to `true` would also block maintainers from direct commits.

If you're a non-maintainer contributor reading this, the bypass doesn't apply to you — your changes still go through a PR. GitHub will block any push to `main` from a non-admin account.

---

## Anatomy of a skill

Every skill folder follows the same layout, so installation is the same everywhere:

```
skills/<skill-name>/
├── SKILL.md              # The instructions the AI agent reads — entry point
├── manifest.json         # Name, description, version, declared deps, required env vars
├── requirements.txt      # (optional) Python deps if the skill has scripts
├── reference.md          # (optional) Long-form reference material
├── examples/             # (optional) Worked examples the agent can study
├── templates/            # (optional) Starter snippets the agent can copy from
├── lenses/               # (optional — devils-advocate style) Checklist files applied as a sweep
├── rubrics/              # (optional — doc-critique style) Per-archetype quality bars
└── scripts/              # (optional) Executable helpers the agent invokes
```

The naming convention for the folder is **kebab-case, descriptive, use-case-first**: `runbook-generator`, not `runbook-helper-v2`. The folder name is the slug Claude Code and other IDEs use for `/`-invocation.

---

## Adding a new skill — step by step

### 1. Decide if it belongs here

skilldrop is for **portable, opinionated artifacts** that knowledge workers and dev teams ship: diagrams, documents, decks, structured critiques, code reviews. A new skill belongs here if:

- ✅ The output is a *concrete artifact* (a doc, diagram, deck, structured review, brief, etc.) — not a chat-style answer.
- ✅ It's *portable* — works in Claude Code today and can be installed into Cursor / Kiro / Continue / Cline / Aider with the documented steps.
- ✅ It's *opinionated* — makes decisions for the user instead of asking five clarifying questions. (See **Voice & tone** below.)
- ✅ It fits one of the existing sections (Pipeline glue · Dev workflow · Diagrams · Documentation · Stakeholder communication) **or** justifies a new section.

It probably doesn't belong here if:

- ❌ It's a generic chat helper that doesn't produce a specific artifact.
- ❌ It depends on a proprietary internal service that contributors can't reach.
- ❌ It's a thin wrapper around a single CLI command (`/run-make` etc.).
- ❌ It duplicates an existing skill — improve the existing one instead.

When in doubt, open an issue with the use case before writing the skill.

### 2. Create the SKILL.md

The `SKILL.md` is the entry point. **Keep it under ~500 lines.** If you need more, split into a sibling `reference.md`, `lenses/`, `rubrics/`, or `templates/` — `SKILL.md` should fit comfortably in an agent's working context without crowding everything else out.

Frontmatter is required:

```yaml
---
name: your-skill-name
description: One sentence, use-case-first. The first half states *what it does*, the second half states *when to use it* (the trigger phrases an AI agent will match on). This is what the LLM reads to decide whether to invoke your skill — write it like a job ad, not like a docstring.
---
```

The body should be sectioned approximately like this — borrow from any existing skill to seed:

```markdown
# skill-name

{One- or two-sentence positioning. What the skill is for, and how it relates to its sibling skills.}

## How to respond

1. **{Imperative verb in bold.}** {The actual instruction.}
2. **{Next step.}** {…}
…

## Useful references in this skill
- [`reference.md`](reference.md) — {one line}
- [`templates/foo.md`](templates/foo.md) — {one line}

## Quality bar
- **{Rule.}** {Why, in one short sentence.}
…

## When to use this skill
- ✅ {Use case}
- ✅ {Use case}

## When NOT to use this skill
- ❌ {Anti-use-case}
- ❌ {Anti-use-case}

## Anti-patterns to avoid
- ❌ {Mistake}
- ❌ {Mistake}
…
```

Not every skill needs every section, but **Quality bar** and **Anti-patterns to avoid** are doing real work — they're what turns a "do this" skill into an "opinionated, ships-good-output" skill. Don't skip them.

### 3. Add the manifest

`manifest.json` is the machine-readable summary. Required fields:

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

- `deps.npm` / `deps.pip` — lists the packages a user must install before the skill works. If the skill has no scripts, leave empty.
- `env.required` — env vars the skill cannot work without (e.g. `FIGMA_TOKEN` for `figma-diagrams`). `env.optional` — vars that change behaviour but aren't required.
- `tags` — 3–6 keywords that help IDEs surface this skill in search and discovery surfaces.

`name` in `manifest.json` **must** match `name` in `SKILL.md` frontmatter and the folder name.

### 4. Add templates, references, lenses, rubrics as needed

The supporting files are where the skill's *content* lives — `SKILL.md` is mostly about *behaviour*.

- **`templates/`** — paste-able starting points (e.g. `templates/madr.md` in adr-generator). Always reference them from `SKILL.md` with a relative link so the agent can find them.
- **`reference.md`** — long-form reference material that doesn't fit in `SKILL.md`. The `architecture-diagrams` and `reverse-architecture` skills use this for notation cheat-sheets and file-to-signal mappings.
- **`lenses/<name>.md`** — checklists applied as a sweep, one lens per file. Used by `devils-advocate`. Each lens file ends with "what this lens is NOT for" so the skill stays focused.
- **`rubrics/<archetype>.md`** — per-archetype quality bars. Used by `doc-critique`. Each rubric mirrors a generator skill's quality bar 1:1.
- **`examples/<name>.md`** — worked examples that show input → output for a non-obvious case. Especially valuable for diagram and deck skills.
- **`scripts/`** — executable helpers. If your skill has scripts, see **Scripts must be portable** below.

### 5. Update the README

Open `README.md` and:

- Add a row to the **Skills in this repo** table (under the right section — or propose a new section in the PR).
- If the skill has runtime deps, add a row to the **Installing dependencies** table.
- If the skill has env vars, mention them inline in the install row.

### 6. Test the skill manually

Before opening a PR, **install your skill into a clean Claude Code instance** and run it end-to-end on at least one realistic input:

```bash
mkdir -p ~/.claude/skills
cp -R skills/your-skill ~/.claude/skills/
```

Then in a new Claude Code session, invoke the skill (`/your-skill <args>` or via natural language) and verify:

- ✅ The agent finds and reads `SKILL.md` without confusion.
- ✅ The output matches the structure described in `Quality bar`.
- ✅ Templates/lenses/rubrics referenced from `SKILL.md` are read at the right moment.
- ✅ Scripts (if any) work from `${CLAUDE_SKILL_DIR}/scripts/…` *and* from a plain relative path (for non-Claude IDEs).
- ✅ Quality-bar items actually get enforced — don't accept a draft from the agent that violates its own quality bar.

If you can, run the skill in a second IDE (Cursor / Continue / Cline) using the installation instructions in the README — that's the cheapest way to catch portability issues.

---

## Voice & tone (the most important section)

skilldrop skills are **opinionated**, not generic. This is the difference between a useful skill and a noisy one. New skills should match the established voice:

### Do

- ✅ **Make decisions for the user.** "Default to MADR. Use Nygard when the user explicitly asks for the classic format." Not "you could consider either MADR or Nygard depending on your preference."
- ✅ **Use concrete examples, not abstract advice.** ❌ "Use clear titles." ✅ "Title is a noun phrase, not a verb phrase. ✅ *'Use Postgres as primary datastore'* — ❌ *'Decide what database to use'*."
- ✅ **Quote and counter-quote.** When showing a rule, show a passing and failing example side by side.
- ✅ **Be specific about anti-patterns.** Every existing skill has an `Anti-patterns to avoid` section. New skills should too. List the *real* mistakes you've seen — not theoretical ones.
- ✅ **Have a "quality bar".** A skill without one is a description, not a generator. Every concrete output should be checkable against the bar.
- ✅ **Use the `✅` / `❌` markers** consistently — they're how the agent reads "this good, that bad" at a glance.
- ✅ **Lead with the rule, then the rationale.** "Title is a noun phrase, not a verb phrase. Why: …" — not "You should think about titles because…"

### Don't

- ❌ **Hedge.** "Generally", "consider", "you might want to", "in most cases" — strip them. If the rule has real exceptions, name them.
- ❌ **Write tutorials.** This isn't documentation; it's instructions to an AI agent. Skip "first, install dependencies" prose — it's in `manifest.json`.
- ❌ **Pad with adjectives.** "Robust, scalable, modern, next-generation" are all noise.
- ❌ **Address the user directly in `SKILL.md`** ("As a contributor, you might…"). The reader is the AI agent. Talk *about* the user in the third person.
- ❌ **Ask 4+ clarifying questions before producing output.** Most skills cap clarifying questions at 2 and pick defaults for everything else.
- ❌ **Use emojis decoratively.** `✅` / `❌` / `🟥` / `🟧` / `🟨` / `⚪` have meaning. Decorative emoji in skill text is noise.

### Description field discipline

The `description` in frontmatter and `manifest.json` is the *most-read* string in your skill — AI agents match the user's prompt against it to decide whether to invoke. Two rules:

- **Lead with the use case, not the implementation.** ✅ "Generate an Architecture Decision Record from a context-decision-consequences brief." — ❌ "Markdown ADR generator using MADR format."
- **End with trigger phrases.** "Use whenever the user wants to capture an architectural decision, write an ADR, or document a 'we decided X because Y' moment." This is what the LLM matches against fuzzy user prompts.

---

## Scripts must be portable

If your skill has executable scripts (Python, Node, shell):

- **Reference them with both `${CLAUDE_SKILL_DIR}/scripts/…` and a plain relative `scripts/…`** in `SKILL.md`. Claude Code sets `CLAUDE_SKILL_DIR`; other IDEs don't.
- **Pin dependencies** in `requirements.txt` (Python) or `package.json` (Node). Don't rely on the user having a specific version installed globally.
- **Read inputs from a file path argument or stdin**, not from a hard-coded Claude Code variable. The script should be runnable as a standalone CLI.
- **Write outputs to a path the user specifies**, not to a hard-coded location.
- **Don't shell out to interactive commands.** No `gh auth login`, no `aws configure` — those need the user; the skill shouldn't try to drive them.

See `skills/deck-builder/scripts/build_deck.py` for the reference pattern.

---

## Pull-request checklist

Before opening a PR, run through this list:

### Branch & merge policy
- [ ] **This PR is from a feature branch**, not from `main`.
- [ ] **Branch is up to date** with `upstream/main` (rebased or merged).
- [ ] **Contributors:** I will not self-merge. Only a maintainer (see [`MAINTAINERS.md`](MAINTAINERS.md)) can approve and merge.
- [ ] **Maintainers:** if self-merging without peer review, the change fits one of the bypass cases in [Maintainer bypass](#maintainer-bypass-when-direct-commits-are-ok) — and I've explained why in the PR description.

### Skill basics
- [ ] **Folder name = SKILL.md `name` = manifest.json `name`.** Kebab-case, no version suffix.
- [ ] **`SKILL.md` is under ~500 lines.** Move long material to `reference.md` / `templates/` / `lenses/` / `rubrics/`.
- [ ] **Quality bar and Anti-patterns sections present** (or there's a real reason they aren't — say so in the PR).
- [ ] **Description leads with the use case** and ends with trigger phrases.
- [ ] **At least one worked example** (`examples/…` or inline) — especially important for diagram, deck, and review skills.
- [ ] **README updated** — table row added, install line added if there are deps.
- [ ] **Manual test pass** — invoked the skill in Claude Code on a realistic input and got an output that meets its own quality bar.
- [ ] **No secrets / personal info** in templates, examples, or test data. Use placeholder data only.
- [ ] **License compatibility** — any code or template adapted from elsewhere is MIT-compatible and attributed if non-trivial.

PR description should include:
- **What the skill does** (one paragraph).
- **One example input and the output it produced** during your manual test pass.
- **Which existing skills it pairs with** (e.g. "downstream of `brief-intake`", "code counterpart to `doc-critique`").

---

## Improving an existing skill

Smaller PRs are easier to merge. Useful kinds of improvements:

- **Tightening the quality bar.** Add a rule you found yourself wishing existed.
- **Adding a worked example.** Especially for skills that don't have one yet.
- **Adding a template.** A new layout for `deck-builder`, a new ADR format for `adr-generator`, a new rubric archetype for `doc-critique`.
- **Catching an anti-pattern.** Found a mistake the skill kept making? Add it to `Anti-patterns to avoid`.
- **Cross-skill polish.** Making sure two skills that pair together (`audience-profile` → `slide-outliner` → `deck-builder`) hand off cleanly.

Note any behavioural change (new templates, new rules, new sections) in the PR description so reviewers can spot-check the affected rubric. Purely stylistic or typo-level changes don't need extra callout.

---

## Proposing a new section in the README

The README currently groups skills as:

1. **Pipeline glue** — skills that connect other skills.
2. **Dev workflow** — skills that act on code.
3. **Diagrams** — visual artifacts.
4. **Documentation** — written technical artifacts.
5. **Stakeholder communication** — artifacts aimed at non-technical audiences.

If your new skill doesn't fit any of these, propose a new section in the PR description with:

- The section name (use-case-first, not technology-first).
- One sentence about what skills belong in it.
- At least one existing skill that would also fit there (or "this is the seed for the section").

Sections are cheap; ungrouped skills are expensive (they make the README harder to scan). Lean toward creating a section once you have two skills that share an axis.

---

## Reporting bugs / proposing skills (without writing code)

Open an issue with:

- **For bugs:** the skill name, the input you gave it, what you expected, what you got. Paste the actual output if you can.
- **For skill proposals:** what's the *concrete artifact* the skill would produce, who would use it, and which existing skills it would pair with. Skills proposed without a clear artifact in mind usually don't get built; ones with a worked example tend to ship.

---

## Tooling we use to maintain skilldrop

- We use `devils-advocate` on our own code changes before shipping.
- We use `doc-critique` on our own `SKILL.md` files before merging new skills — every new skill should pass its own rubric.
- We use `brief-intake` to triage incoming issues into structured proposals.

If you're contributing, the same skills are available to you. Eating our own dog food keeps them honest.

---

## License

By contributing, you agree your contributions are licensed under the MIT License (see [LICENSE](LICENSE)).
