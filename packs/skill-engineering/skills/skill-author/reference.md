# skill-author reference

## How a tool reads a skill

Every tool that supports Agent Skills loads them in three stages, and that order sets the
writing priorities:

1. **At startup it reads only `name` and `description`** from every installed skill. This is
   the routing decision. A skill whose description loses here is never read.
2. **When a request matches, it reads the SKILL.md body.** This is where the steps, quality
   bar and boundaries live.
3. **It reads reference files and runs scripts only when a step points to them.** That is
   why every reference file must be linked from SKILL.md, and why long material can live
   outside SKILL.md at no cost until it's needed.

## Frontmatter

```yaml
---
name: release-notes-from-prs
description: Write customer-facing release notes from merged pull requests — … Use when the user …
---
```

| Field | Rule |
|---|---|
| `name` | Required. Lowercase letters, digits and single hyphens, at most 64 characters, identical to the folder name. |
| `description` | Required. At most 1,024 characters. Leads with the artifact, ends with trigger phrases. |
| Others | The Agent Skills specification also defines optional fields such as `license` and `metadata`. Claude Code reads extras such as `allowed-tools`; other tools ignore fields they don't know. Add one only when you know which tool reads it, and say in SKILL.md what happens in the others. |

## Writing the description

The formula: **artifact and use case → two or three distinguishing details → trigger phrases.**

| Rule | ✅ | ❌ |
|---|---|---|
| Lead with the artifact, as a verb and a noun | "Write a threat model for…" | "This skill helps teams think about security" |
| Name what sets it apart from the nearest sibling | "…from merged PRs, internal changes dropped" | "…for releases" |
| End with phrases users type, in quotes | `says "write the release notes", "draft the changelog"` | "Use for release management workflows" |
| Name the input when it's distinctive | "from a transcript or rough notes" | "from information" |
| No hype | "grouped New / Improved / Fixed" | "powerful, comprehensive release tooling" |
| One artifact | "release notes" | "release notes, roadmaps and status reports" |

**Testing against siblings.** For each near-miss sibling, take one of its should-trigger
queries and ask which description wins it. If yours does, add the words that separate them
("for customers, not the team"; "from PRs, not from a roadmap"). Then add a When NOT line
naming the sibling, and a should-not-trigger query using that sibling's request.

**Length.** 250–600 characters names the artifact, the details and four or five triggers.
Under ~120 rarely does both. Near 1,024 usually means the skill does too much.

## Body rules

- **Third person for the user, imperative for the agent.** "Ask the user for…", not "You might
  want to ask…".
- **Steps decide.** Pick defaults. Strip "generally", "consider", "you might want to". If a
  rule has an exception, name it.
- **Ask once.** Step 1 gathers every missing input in one message with defaults shown. At most
  two real questions.
- **Show a passing and a failing example** wherever a rule could be read two ways.
- **Quality bar items are checkable** against one output. "High quality" is not checkable;
  "every line carries a PR number from the input" is.
- **When NOT lines name the alternative**: a sibling skill, a tool, or "a plain prompt".
- **Anti-patterns are real mistakes** seen in this task, not "don't be vague".
- **A skill never invokes another skill.** Name a sibling as a next step; the user or a
  workflow runs it. A copied skill must work alone.

## Splitting files

| File | Put here |
|---|---|
| `SKILL.md` | The steps, the rules that apply every run, the boundaries. Under ~500 lines. |
| `reference.md` or a `references/` folder | Lookup tables, long rubrics, catalogues, domain background. |
| a `templates/` folder | Output skeletons the agent fills. |
| an `examples/` folder | One worked input → output, for a skill where "good" is hard to describe. |
| a `scripts/` folder | Code for exact work. |
| an `evals/` folder | `evals.json` and `eval_queries.json`. |

Link every reference file from SKILL.md with a relative link. A reference file over ~1,000
lines needs a table of contents at the top.

## The script contract

- Standard library only, unless the job truly needs a package; then declare it in a
  `requirements.txt` and say so in SKILL.md.
- Input from arguments or stdin. Output to a path the user gives, never into the skill folder
  or a fixed location.
- Exit non-zero with a one-line message on bad input.
- No network calls unless fetching is the skill's purpose and SKILL.md says so.
- Shown in SKILL.md both ways: `"${CLAUDE_SKILL_DIR}/scripts/<script>.py"` for Claude Code,
  and the same path relative to the skill folder for every other tool.
- Tested on a real input and a bad one. Example outputs are pasted from real runs.

## Where each tool reads skills

| Tool | Project scope | Personal scope |
|---|---|---|
| Claude Code | `.claude/skills/<name>/` | `~/.claude/skills/<name>/` |
| Codex | `.agents/skills/<name>/` | `~/.codex/skills/<name>/` |
| Antigravity | `.agents/skills/<name>/` | `~/.gemini/antigravity-cli/skills/<name>/` |
| GitHub Copilot | `.github/skills/<name>/` (Copilot CLI also reads `.claude/skills/` and `.agents/skills/`) | `~/.copilot/skills/<name>/` |
| Kiro (IDE and CLI) | `.kiro/skills/<name>/` | `~/.kiro/skills/<name>/` |
| Cursor | Copy the folder to `.cursor/skills/<name>/` and add a rule at `.cursor/rules/<name>.mdc` whose `description` is the skill's description and whose body says to follow that SKILL.md | — |
| Continue, Cline, Aider | Copy the folder anywhere in the repo and attach `SKILL.md` to the prompt (`@file`, or `/add` in Aider) | — |

Copy the whole folder, never its parent, and keep the layout intact so relative paths
resolve. For a team repo, one copy in `.agents/skills/` reaches Codex, Antigravity and
Copilot CLI; add `.claude/skills/` for Claude Code.

## Eval formats

`evals/evals.json`:

```json
{
  "skill_name": "release-notes-from-prs",
  "evals": [
    {
      "id": 1,
      "prompt": "Write the release notes for Acme Tasks v2.4 from these merged PRs: …",
      "assertions": [
        "Breaking changes appear first, each with an action the user must take",
        "The output does not invent a change that no PR in the prompt supports"
      ]
    }
  ]
}
```

`evals/eval_queries.json`:

```json
[
  {"query": "Write the release notes for v2.4 from these merged PRs", "should_trigger": true},
  {"query": "Write the launch blog post for the export feature", "should_trigger": false}
]
```

At least four `true` rows in different wordings and three or four `false` rows, each a
request a named sibling handles. A `false` row nobody would type tests nothing.

To run them by hand: install the skill, start a fresh session, paste each eval prompt, and
mark each assertion pass or fail. For the queries, check that each `true` row picks the skill
and each `false` row picks something else.
