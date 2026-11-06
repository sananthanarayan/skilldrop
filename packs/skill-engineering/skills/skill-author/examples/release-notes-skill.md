# Example: from a described task to a finished skill

## Input

> Every release I paste our merged PRs into the chat and ask for customer-facing notes, and
> every time I have to explain the format again. Can you make this a skill? We use Claude Code
> and Copilot at Acme. We already have `sprint-status` and `launch-post` skills in the repo.

## The interview (one message)

The user had already given the tools, the repo and two siblings, so the interview asked only
for the gaps:

> Before I write it, three things. Reply "go" to take the defaults.
> 1. **What makes the notes good?** *Default: grouped New / Improved / Fixed, breaking changes
>    first, one line per PR in user terms with the PR number, internal changes dropped.*
> 2. **What would you type to ask for it?** *Default: "write the release notes", "draft the
>    changelog for v2.4", "what shipped this sprint, for customers".*
> 3. **Anything it must never make up?** *Default: changes or benefits that no PR states.*

The user replied: "go, and breaking changes need a 'what to do' line."

## Decisions made without asking

- **It is a skill:** a repeatable task with one artifact. Not an AGENTS.md rule.
- **Name:** `release-notes-from-prs`. The input is in the name because "release notes" alone
  would also claim roadmap-driven announcements, which belong to `launch-post`.
- **No script.** Sorting and rewriting PR titles is judgment, not arithmetic.
- **Boundaries:** the sprint report goes to `sprint-status`, the announcement to
  `launch-post`. Each appears in When NOT to use and as a should-not-trigger query.
- **Install:** `.claude/skills/` for Claude Code, which Copilot CLI also reads. Add
  `.github/skills/` for Copilot in the editor.

## Output

```
.claude/skills/release-notes-from-prs/
├── SKILL.md
├── templates/release-notes.md
└── evals/
    ├── evals.json
    └── eval_queries.json
```

### `SKILL.md`

```markdown
---
name: release-notes-from-prs
description: Write customer-facing release notes from a list of merged pull requests — grouped into New, Improved and Fixed, each line in user terms with the PR number, internal-only changes dropped, and breaking changes called out first. Use when the user pastes merged PRs or a git log and says "write the release notes", "draft the changelog for v2.4", or "what shipped this sprint, for customers".
---

# release-notes-from-prs

You turn a list of merged pull requests into release notes a customer can read in a minute.
The input is engineering language; the output says what changed for the person using the
product. Internal changes (refactors, CI, dependency bumps with no user effect) are dropped,
and the user sees the list of what was dropped.

## How to respond

1. **Ask once for what's missing.** You need the merged PRs (titles, numbers, and bodies or
   labels if available), the version and release date, and the audience (end users or
   developers using an API). Ask in one message; default the audience to end users.
2. **Sort every PR into one bucket:** Breaking, New, Improved, Fixed, or Internal. A PR with
   a `breaking` label or a removed option goes to Breaking even if it also adds something.
3. **Rewrite each kept PR as one line in user terms.** ✅ *"Exports now include the time zone
   (#412)"* ❌ *"Refactor ExportSerializer to pass tz (#412)"*. Keep the PR number.
4. **Put Breaking first**, each with what the user must do. A breaking change with no action
   line is not finished.
5. **Fill [`templates/release-notes.md`](templates/release-notes.md)** and list the dropped
   Internal PRs under the notes, so the user can overrule you.

**Non-interactive runs** (subagent, CI, headless): with no PR list, emit
`BLOCKED: need the merged PRs (titles and numbers)` and write nothing. A missing version or
date becomes `[assumption] version: unreleased`.

## Useful references in this skill

- [`templates/release-notes.md`](templates/release-notes.md) — the release-notes skeleton

## Quality bar

- **Every line traces to a PR number** from the input. Nothing is added that no PR supports.
- **Lines are in user terms**: what changed for the user, not which class changed.
- **Breaking changes come first** and each carries the action the user must take.
- **Dropped PRs are listed**, so nothing disappears silently.

## When to use this skill

- ✅ Release notes or a changelog entry from merged PRs or a git log
- ✅ A "what shipped" summary for customers at the end of a sprint

## When NOT to use this skill

- ❌ An internal sprint report for the team: use `sprint-status`
- ❌ A launch announcement or blog post, which needs positioning, not a list: use `launch-post`

## Anti-patterns to avoid

- ❌ **Copying PR titles verbatim.** "Bump lodash to 4.17.21" means nothing to a customer.
- ❌ **Hiding a breaking change under Improved** because it also adds a feature.
- ❌ **Inventing a benefit** ("faster exports") that no PR measured.
```

### `templates/release-notes.md`

```markdown
# {Product} {version} — {YYYY-MM-DD}

## Breaking changes
- {what changed} — **what to do:** {action} (#{n})

## New
- {line in user terms} (#{n})

## Improved
- {line} (#{n})

## Fixed
- {line} (#{n})

---
Dropped as internal: #{n} {title}, …
```

### `evals/evals.json`

```json
{
  "skill_name": "release-notes-from-prs",
  "evals": [
    {
      "id": 1,
      "prompt": "Write the release notes for Acme Tasks v2.4 (shipping 2026-10-15) from these merged PRs: #401 Add CSV export for boards; #405 Remove legacy v1 API tokens (breaking); #407 Refactor board serializer; #409 Fix due dates shifting a day for users in UTC-8; #410 Bump eslint to 9.1.",
      "assertions": [
        "The removal of v1 API tokens (#405) appears first, under Breaking, with an action the user must take",
        "Every line carries a PR number from the prompt, and no line describes a change that no PR supports",
        "#407 and #410 are dropped as internal and listed under the notes",
        "The due-date fix is written in user terms, not as the code change",
        "No performance or benefit claim appears that the PR titles do not state"
      ]
    }
  ]
}
```

### `evals/eval_queries.json`

```json
[
  {"query": "Write the release notes for v2.4 from these merged PRs", "should_trigger": true},
  {"query": "Draft the changelog entry from this git log", "should_trigger": true},
  {"query": "What shipped this sprint? Make it readable for customers", "should_trigger": true},
  {"query": "Turn these PR titles into customer-facing notes for the release", "should_trigger": true},
  {"query": "Write the launch blog post for our new export feature", "should_trigger": false},
  {"query": "Give me a status update on the sprint for the engineering manager", "should_trigger": false},
  {"query": "Review this pull request for bugs before I merge it", "should_trigger": false}
]
```

### Install

```bash
mkdir -p .claude/skills .github/skills
cp -R release-notes-from-prs .claude/skills/     # Claude Code, and Copilot CLI
cp -R release-notes-from-prs .github/skills/     # Copilot in the editor
```

### Check

The folder was linted with `skill-review`'s script, against the two sibling skills in the
same repo. This is the real output:

```
$ python3 lint_skill.py release-notes-from-prs --siblings .
lint_skill: release-notes-from-prs  (release-notes-from-prs)
  skill_md_lines=57  description_chars=388  evals=1  assertions=5  trigger_queries=4  near_miss_queries=3  siblings_compared=2
  closest: sprint-status 0.07, launch-post 0.05
  no findings
result: 0 error(s), 0 warning(s), 0 info -> mechanical checks pass
```

The lint passing covers only the mechanical checks. Next: run the eval prompt in a fresh
session and mark each assertion.
