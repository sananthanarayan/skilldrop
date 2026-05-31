# agents

Portable **reviewer agents** — opinionated personas you delegate code and test review to. Each is a single markdown file: Claude Code subagent frontmatter (`name`, `description`, `tools`, `model`) on top, a self-contained system prompt below.

The frontmatter makes the file a drop-in **Claude Code subagent**. The body is plain enough to paste into any other tool's agent / mode / system-prompt slot. No tool auto-discovers a folder literally named `agents/` — this folder is the **canonical source of truth**, and the table below tells you where to copy each file for your tool.

## The agents

| Agent | Reviews for | Question it answers |
|---|---|---|
| [`devils-advocate`](devils-advocate.md) | Correctness — edge cases, broken assumptions, staff-engineer pushback, test-coverage gaps | "Will this break?" |
| [`code-quality`](code-quality.md) | Craft — naming, structure, duplication, needless complexity, readability | "Will the next engineer hate this?" |

They are deliberately **split, not merged.** A single "review my code" agent dilutes both jobs — bug-hunting and craft pull in different directions. Run them as two passes. `devils-advocate` here is the subagent form of the [`devils-advocate` skill](../skills/devils-advocate/SKILL.md); same persona, packaged for a tool's native agent slot instead of on-demand skill invocation.

## Installing an agent into your tool

### Claude Code (native subagents)

Claude Code reads subagents from `.claude/agents/`. Copy the file in as-is — the frontmatter is already correct:

```bash
# project-scope (shared with the team via the repo)
mkdir -p .claude/agents && cp agents/devils-advocate.md .claude/agents/

# user-scope (every project on your machine)
mkdir -p ~/.claude/agents && cp agents/code-quality.md ~/.claude/agents/
```

Then delegate by name — "use the devils-advocate agent on this diff" — or let Claude Code auto-route based on the `description`. Each subagent runs in its own context window.

### Cursor (custom modes / rules)

Cursor has no subagent file format. Two options:

- **Custom mode** (cleanest): Settings → Chat → Custom Modes → New. Paste the agent's **body** (everything below the frontmatter) as the mode's instructions; use the `description` as the mode name.
- **Project rule**: create `.cursor/rules/<agent>.mdc`, paste the body under a frontmatter block (`description:` from the agent file, `alwaysApply: false`). Invoke by attaching it with `@` or describing the review task.

### Codex (`AGENTS.md`)

Codex reads a single `AGENTS.md` instruction file and has no subagent concept. Either:

- Paste the agent body into a clearly headed section of `AGENTS.md` (e.g. `## Devil's-advocate review`) and trigger it with "run the devil's-advocate review on this diff", or
- Keep the file at `agents/devils-advocate.md` and start the review turn with "Follow the instructions in `agents/devils-advocate.md` for the diff below."

### Kiro (steering files / custom agents)

- **Custom agent** (cleanest): paste the agent body into a new Kiro custom-agent definition; use the `description` as its summary.
- **Steering file**: drop the file at `.kiro/steering/<agent>.md` so Kiro applies it as context, then ask for the review by name.

### Continue, Cline, Aider, and other tools

No standard agent directory. Two patterns work everywhere:

- **Context attachment** — keep the file in the repo and attach it to the review turn (Continue/Cline `@file`, Aider `/add agents/<agent>.md`), then tell the tool to follow it.
- **Custom prompt** — paste the agent body into the tool's custom-prompt / system-prompt config. The `description` field is a good seed for the agent's name.

## Adding a new agent

1. Create `agents/<name>.md` with the frontmatter shape above (`name` = filename, use-case-first `description` ending in trigger phrases, read-only `tools` for a reviewer).
2. Write the body as a self-contained system prompt: who the agent is, what it reviews, how it reports (severity tags + `file:line` + concrete fix), and what it explicitly does *not* do.
3. Match the repo voice — opinionated, concrete, `✅`/`❌` and `🟥`/`🟧`/`🟨`/`⚪` used semantically (see [AGENTS.md](../AGENTS.md)).
4. Add a row to **The agents** table above.
