# agents

Portable **reviewer agents** — opinionated personas you delegate code and test review to. Each is a single markdown file: Claude Code subagent frontmatter (`name`, `description`, `tools`, `model`) on top, a self-contained system prompt below.

The frontmatter makes the file a drop-in **Claude Code subagent**. The body is plain enough to paste into any other tool's agent / mode / system-prompt slot.

Nothing auto-discovers *this* folder at the repo root, so it is the **canonical source of truth**. As of the [July 2026 survey](../docs/designs/ide-primitive-coverage.md), **five tools have a native subagent format** — Claude Code, Kiro, Codex, Copilot, and Antigravity, which registers subagents from a directory literally named `agents/` inside a plugin bundle.

**The CLI installs into four of them** ([RFC-0012](../docs/rfcs/0012-subagent-installation.md)):

```bash
npx skilldrop-cli agents                                       # list
npx skilldrop-cli install --agent devils-advocate              # ~/.claude/agents/
npx skilldrop-cli install --agent devils-advocate --ide kiro   # .kiro/agents/*.json
```

**Five of the five tools with a native format now install by command** — Claude Code, Kiro, Codex, Copilot, and Antigravity. Only Cursor needs hand-work, because it has no agent file format at all. Each section below gives the command where one exists, and the manual route either way.

## The agents

| Agent | Reviews for | Question it answers |
|---|---|---|
| [`devils-advocate`](devils-advocate.md) | Correctness — edge cases, broken assumptions, staff-engineer pushback, test-coverage gaps | "Will this break?" |
| [`code-quality`](code-quality.md) | Craft — naming, structure, duplication, needless complexity, readability | "Will the next engineer hate this?" |
| [`security-reviewer`](security-reviewer.md) | Security — authz, injection, secret exposure, SSRF, unsafe deserialization, weak crypto, risky deps | "What can an attacker do with this?" |

They are deliberately **split, not merged.** A single "review my code" agent dilutes all three — bug-hunting, craft, and exploitability pull in different directions. Run them as separate passes; together they are the reviewer panel [`feature-implement-loop`](../skills/feature-implement-loop/SKILL.md) drives after each generation round. `devils-advocate` here is the subagent form of the [`devils-advocate` skill](../skills/devils-advocate/SKILL.md); same persona, packaged for a tool's native agent slot instead of on-demand skill invocation.

## Fire them as a panel

The three reviewers are meant to run **together** on a change. Install the whole fleet in one command:

```bash
npx skilldrop-cli install --panel review            # 3 subagents + the pre-merge-review orchestrator -> ~/.claude/
npx skilldrop-cli install --panel review --project  # .claude/ (shared with the repo)
```

The [`pre-merge-review`](../skills/pre-merge-review/SKILL.md) skill is the **portable orchestrator** — it dispatches the three as **parallel subagents** where the tool has a native subagent runner, and sweeps the lenses inline otherwise. The orchestration lives in the *skill* (portable); the reviewers are *native subagents* (per-tool):

| Tool | How the panel fires in parallel |
|---|---|
| **Claude Code** | Native parallel subagents — `pre-merge-review` fires all three at once. `--panel review` installs both halves. |
| **Kiro** | Native subagents — `--panel review --ide kiro` installs both halves. |
| **Codex** | Multi-agent runner — install the agents (`--agent … --ide codex`) + the skill; Codex runs the fleet in parallel (confirm the invocation against your Codex version). |
| **Antigravity** | Lead → specialist delegation — install the agents (`--agent … --ide antigravity`) + the skill; the lead agent delegates to the three, each in its own context. |
| **Copilot** | Agents install (`--agent … --ide copilot`); the skill drives them — sequentially unless your Copilot build exposes parallel subagents. |
| **Cursor** | No agent format — `pre-merge-review` sweeps the three lenses inline (no subagents). |

Designing your own fleet? Use [`subagent-design`](../skills/subagent-design/SKILL.md) — the reviewer panel is its "judge panel" topology.

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

```bash
npx skilldrop-cli install --agent devils-advocate --ide kiro   # .kiro/agents/<name>.json
```

Kiro reads JSON agent definitions from `.kiro/agents/` (local) or `~/.kiro/agents/` (global). The emitter maps Claude Code tool names to [Kiro's built-ins](https://kiro.dev/docs/cli/reference/built-in-tools/) — `Read`/`Grep`/`Glob`/`Bash` → `read`/`grep`/`glob`/`shell` — and **names any tool it cannot map** rather than dropping it silently.

Two choices worth knowing if you hand-write one instead:

- **The prompt is inlined, not a `file://` reference.** Kiro's docs show a relative `file://` path but do not say whether it resolves against the workspace root or the JSON file, and a wrong path fails *silently* — the agent loads with no instructions.
- **`allowedTools` is omitted**, so you are prompted per tool call. That is the right default for a reviewer, and it avoids [kirodotdev/Kiro#6714](https://github.com/kirodotdev/Kiro/issues/6714), where the field does not load as configured.

**Don't use a steering file for this.** Earlier advice here said to drop the agent at `.kiro/steering/<agent>.md`; a steering file with no inclusion mode is loaded into *every* session, which is a permanent context cost for a persona you want on demand. Same reason the CLI stopped writing steering shims for skills.

### GitHub Copilot (native custom agents)

```bash
npx skilldrop-cli install --agent devils-advocate --ide copilot   # .github/agents/<name>.agent.md
```

Copilot reads `.github/agents/<name>.agent.md` (repo) or `~/.copilot/agents/` (personal). The filename minus `.agent.md` is the invocation name — `copilot --agent devils-advocate`. The install is a pure rename; nothing in the file changes.

### Antigravity CLI (plugin subagents)

```bash
npx skilldrop-cli install --agent devils-advocate --ide antigravity   # ~/.gemini/config/agents/
```

Antigravity discovers subagents at `~/.gemini/config/agents/<name>.md` (global) or `.agents/agents/<name>.md` (workspace, `--project`) — markdown with YAML frontmatter, same shape as these files. A plugin bundle is a *third* option, not a requirement; [RFC-0013](../docs/rfcs/0013-antigravity-plugin-bundle.md) records why an earlier draft wrongly thought it was the only one.

The emitter adds **`subagent: true`** — without it the agent exists but `invoke_subagent` cannot reach it — and maps `Read`/`Grep`/`Bash` to `view_file`/`grep_search`/`run_command`. Antigravity has no glob-style tool, so `Glob` is named and dropped rather than bent into `list_dir`.

### Continue, Cline, Aider, and other tools

No standard agent directory. Two patterns work everywhere:

- **Context attachment** — keep the file in the repo and attach it to the review turn (Continue/Cline `@file`, Aider `/add agents/<agent>.md`), then tell the tool to follow it.
- **Custom prompt** — paste the agent body into the tool's custom-prompt / system-prompt config. The `description` field is a good seed for the agent's name.

## Adding a new agent

1. Create `agents/<name>.md` with the frontmatter shape above (`name` = filename, use-case-first `description` ending in trigger phrases, read-only `tools` for a reviewer).
2. Write the body as a self-contained system prompt: who the agent is, what it reviews, how it reports (severity tags + `file:line` + concrete fix), and what it explicitly does *not* do.
3. Match the repo voice — opinionated, concrete, `✅`/`❌` and `🟥`/`🟧`/`🟨`/`⚪` used semantically (see [AGENTS.md](../AGENTS.md)).
4. Add a row to **The agents** table above.
