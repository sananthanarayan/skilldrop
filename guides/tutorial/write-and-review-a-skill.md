---
title: Write a skill your whole team can install, then review one before you trust it
summary: Turn a task you keep re-explaining to your agent into a portable skill folder with evals, then audit a teammate's skill that would have hidden where it saved files and run remote code, with the skill-engineering pack.
kind: tutorial
---

# Write a skill your whole team can install, then review one before you trust it

In about twenty minutes you'll turn a task you keep explaining to your agent into a skill
folder that Claude Code, Copilot, Codex, Cursor and Kiro can all load. Then you'll review a
skill a teammate wants to share, and find that it tells the agent to hide where it saved
your files and runs a script downloaded from the internet.

Both examples ship with the skills. The lint output below is the review script's real
output.

## Install the pack

```bash
npx skilldrop-cli install --pack skill-engineering
```

This adds `skill-author` and `skill-review`, plus `core`.

## Describe the task you keep re-explaining

Say what it produces, how you ask for it, and which skills sit next to it:

> Every release I paste our merged PRs into the chat and ask for customer-facing notes, and
> every time I have to explain the format again. Can you make this a skill? We use Claude
> Code and Copilot. We already have `sprint-status` and `launch-post` skills in the repo.

## Answer one round of questions

`skill-author` asks only for what you didn't say, in one message, with a default for each:

> 1. **What makes the notes good?** *Default: grouped New / Improved / Fixed, breaking
>    changes first, one line per PR in user terms with the PR number, internal changes
>    dropped.*
> 2. **What would you type to ask for it?**
> 3. **Anything it must never make up?** *Default: changes or benefits that no PR states.*

Reply "go, and breaking changes need a 'what to do' line." The rest it decides and tells you.
The name is `release-notes-from-prs`, because "release notes" alone would also claim the
announcements that belong to `launch-post`. It has no script, because rewriting PR titles is
judgement, not arithmetic.

## Read what it wrote

```text
.claude/skills/release-notes-from-prs/
├── SKILL.md
├── templates/release-notes.md
└── evals/
    ├── evals.json
    └── eval_queries.json
```

Open `SKILL.md` and read the description first. It's the line an agent matches your request
against. It names the artifact and ends with the phrases you'd type, so "write the release
notes" routes here and "what did the team ship this sprint" routes to `sprint-status`.
`eval_queries.json` has phrasings that should trigger the skill and near-misses that should
go to each sibling. That's how you'll know routing still works after the next edit.

## Install it for both tools

```bash
mkdir -p .claude/skills .github/skills
cp -R release-notes-from-prs .claude/skills/     # Claude Code, and Copilot CLI
cp -R release-notes-from-prs .github/skills/     # Copilot in the editor
```

## Lint it against its siblings

> Review release-notes-from-prs against the other skills in .claude/skills.

`skill-review` runs its lint script first:

```text
lint_skill: release-notes-from-prs  (release-notes-from-prs)
  skill_md_lines=57  description_chars=388  evals=1  assertions=5  trigger_queries=4  near_miss_queries=3  siblings_compared=2
  closest: sprint-status 0.07, launch-post 0.05
  no findings
result: 0 error(s), 0 warning(s), 0 info -> mechanical checks pass
```

`closest` is how much its description overlaps each sibling's; low numbers mean the router
won't confuse them. A clean lint covers the mechanical checks only. Run the eval prompt in a
fresh session and mark each assertion before you share the skill.

## Review a teammate's skill before you install it

A teammate wants to share `meeting-notes`. Its description is "This skill helps with meeting
notes." Its steps fetch formatting rules from a URL. They save to a path under the author's
own home folder, and they tell the agent not to say where the notes went. Its script reads
an API token and pipes a downloaded install script into a shell.

> Review the meeting-notes skill before I install it.

The lint finds 7 errors and 12 warnings. These are the lines that matter most:

```text
  ERROR safety       conceal-from-user: tells the agent to hide actions from the user [AST01, LLM01]  (SKILL.md:10)
  ERROR safety       exec-remote: downloads and executes remote content [AST01, AST02]  (scripts/summarise.py:3)
  ERROR portability  ${CLAUDE_SKILL_DIR}/scripts/summarise.py has no plain relative fallback; only Claude Code sets that variable, so Codex, Copilot, Cursor and Kiro cannot find the file  (SKILL.md)
  WARN  safety       remote-instructions: tells the agent to fetch instructions from a URL at run time; what it obeys can change after review [AST05, LLM01]  (SKILL.md:8)
result: 7 error(s), 12 warning(s), 1 info -> mechanical checks FAIL
```

The codes in brackets map each finding to the OWASP agentic-skills and LLM top-10 lists. The
review then gives its verdict:

> **REWRITE** — 4 blocker, 4 major, 3 minor, 0 nit. The script installs and runs remote code,
> and the remote rules file means what the agent obeys can change after anyone reviews it.

Each finding comes with its line and a fix. The fix for the script is to delete it:
summarising a transcript needs no code. The verdict is one of READY, FIX FIRST or REWRITE.
A REWRITE goes back to `skill-author`, built around one artifact.

## What you have now

A skill folder your team installs the same way in every tool, with evals to rerun when it
changes, and a review that names what a shared skill would make your agent do before you
let it. Run `skill-review` on any skill before you install it, including skills from this
catalogue.

Next: [Use the skill-engineering pack](../how-to/packs/use-the-skill-engineering-pack.md), or
[Author a skill](../how-to/author-a-skill.md) for a skill in this repository.
