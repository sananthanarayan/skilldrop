# agents

Portable **reviewer agents** — opinionated personas you delegate code and test review to. Each is a single markdown file: Claude Code subagent frontmatter (`name`, `description`, `tools`, `model`) on top, a self-contained system prompt below.

The frontmatter makes the file a drop-in **Claude Code subagent**. The body is plain enough to paste into any other tool's agent / mode / system-prompt slot.

Nothing auto-discovers *this* folder at the repo root, so it is the **canonical source of truth** and the table below says where to copy each file. That framing used to be simpler: as of the [July 2026 survey](../docs/designs/ide-primitive-coverage.md), **five tools have a native subagent format** — Claude Code, Kiro, Codex, Copilot, and Antigravity, which registers subagents from a directory literally named `agents/` inside a plugin bundle. The CLI does not install agents into any of them yet ([RFC-0010](../docs/rfcs/0010-install-target-table.md) has to settle the projection model first), so copying by hand remains the route.

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

### Codex (native subagents)

```bash
npx skilldrop-cli install --agent devils-advocate --ide codex   # ~/.codex/agents/<name>.toml
```

Standalone TOML in `~/.codex/agents/` or `.codex/agents/` (`--project`). Codex requires `name`, `description`, and `developer_instructions`, and **rejects unknown fields** — so the emitter writes exactly those three. It leaves `sandbox_mode` unset, which means the agent inherits the parent session's permissions; Codex has no `tools` field, and guessing a sandbox value would either break the agent or silently widen what it can do.

### Kiro (native custom agents)

Kiro reads JSON agent definitions from `.kiro/agents/` (local) or `~/.kiro/agents/` (global). The filename minus `.json` becomes the agent's name.

Its `prompt` field accepts a **`file://` URI**, so the definition can point at the markdown instead of duplicating it — the cleanest projection of any tool surveyed:

```json
{
  "name": "devils-advocate",
  "description": "<paste the description from the agent's frontmatter>",
  "prompt": "file://./agents/devils-advocate.md",
  "tools": ["read", "grep", "execute"]
}
```

**Don't use a steering file for this.** Earlier advice here said to drop the agent at `.kiro/steering/<agent>.md`; a steering file with no inclusion mode is loaded into *every* session, which is a permanent context cost for a persona you want on demand. Same reason the CLI stopped writing steering shims for skills.

### GitHub Copilot (native custom agents)

Copilot reads `.github/agents/<name>.agent.md` (repo) or `~/.copilot/agents/` (personal). The filename minus `.agent.md` is the invocation name — `copilot --agent devils-advocate`. Copy the file in and rename it; the frontmatter needs `name` and `description`, and takes an optional `tools` list.

### Antigravity CLI (plugin subagents)

Antigravity registers subagent templates from an `agents/` directory **inside a plugin bundle** at `~/.gemini/antigravity-cli/plugins/<plugin>/agents/`. There is no project-root `agents/` convention, so this is a copy into a bundle you own, not a drop-in.

### Continue, Cline, Aider, and other tools

No standard agent directory. Two patterns work everywhere:

- **Context attachment** — keep the file in the repo and attach it to the review turn (Continue/Cline `@file`, Aider `/add agents/<agent>.md`), then tell the tool to follow it.
- **Custom prompt** — paste the agent body into the tool's custom-prompt / system-prompt config. The `description` field is a good seed for the agent's name.

## Adding a new agent

1. Create `agents/<name>.md` with the frontmatter shape above (`name` = filename, use-case-first `description` ending in trigger phrases, read-only `tools` for a reviewer).
2. Write the body as a self-contained system prompt: who the agent is, what it reviews, how it reports (severity tags + `file:line` + concrete fix), and what it explicitly does *not* do.
3. Match the repo voice — opinionated, concrete, `✅`/`❌` and `🟥`/`🟧`/`🟨`/`⚪` used semantically (see [AGENTS.md](../AGENTS.md)).
4. Add a row to **The agents** table above.
