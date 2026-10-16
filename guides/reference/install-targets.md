---
title: Install targets and dependencies
summary: Where each install target puts skills and subagents, the by-hand steps for Claude Code, Cursor, Kiro and agents without a skills folder, what --local does, and each skill's dependency install.
kind: reference
---

# Install targets and dependencies

The paths and per-tool details behind [Install a skill into your IDE](../how-to/install-per-ide.md). Commands and flags are on [Install options](install-options.md).

## Manual install

Each skill is a plain directory, and installing one is always two steps: copy the skill folder into your IDE's skills or rules location, then install the skill's dependencies (the packages are in `manifest.json` under `deps`; see [Installing dependencies](#installing-dependencies)). You can also copy the companions listed under `related` in the skill's `manifest.json`. Skills reference each other, and a hand-off to an uninstalled sibling degrades to inline guidance, but the pipelines work best complete.

## Skill targets

Pick one target per `install`, `update` or `uninstall`:

| Flag | Writes to | For |
|---|---|---|
| *(default)* | `~/.claude/skills/` | Claude Code, user scope |
| `--project` | `./.claude/skills/` | Claude Code and GitHub Copilot CLI, project scope |
| `--local` | project scope, hidden from git | trying skills in a repo you don't own; see [below](#local-installs-in-a-repo-you-dont-own) |
| `--ide cursor` | `./.cursor/skills/` + `.cursor/rules/<skill>.mdc` | Cursor |
| `--ide kiro` | `./.kiro/skills/` | Kiro IDE and Kiro CLI, discovered natively |
| `--ide codex` | `~/.codex/skills/` (`--project`: `./.agents/skills/`) | Codex |
| `--ide antigravity` | `~/.gemini/antigravity-cli/skills/` (`--project`: `./.agents/skills/`) | Antigravity CLI |
| `--ide copilot` | `~/.copilot/skills/` (`--project`: `./.github/skills/`) | GitHub Copilot |
| `--dest <dir>` | any directory | Continue, Cline, Aider and others |

## Claude Code

Claude Code reads skills from two locations:

- **User scope** (available in every project): `~/.claude/skills/<skill-name>/`
- **Project scope** (tracked with the repo): `<project>/.claude/skills/<skill-name>/`

Copy the skill directory itself into the skills location, **not** its parent pack folder:

```bash
# user scope (for personal use)
mkdir -p ~/.claude/skills
cp -R packs/solution-architect/skills/architecture-diagrams ~/.claude/skills/
cp -R packs/solution-architect/skills/figma-diagrams ~/.claude/skills/

# project scope (for sharing with a team)
mkdir -p .claude/skills
cp -R packs/solution-architect/skills/architecture-diagrams .claude/skills/
cp -R packs/solution-architect/skills/figma-diagrams .claude/skills/
```

Claude Code discovers the skill through the `name` field in its `SKILL.md` frontmatter. Invoke it in chat with `/<skill-name>` or by describing the task, and Claude routes to the matching skill.

## Cursor

Cursor has no native skills concept; a skill installs as a **project rule**. `--ide cursor` does these steps for you. By hand:

1. Copy the skill folder somewhere in the repo, for example `.cursor/skills/<skill-name>/`:
   ```bash
   mkdir -p .cursor/skills
   cp -R packs/solution-architect/skills/architecture-diagrams .cursor/skills/
   ```

2. Create `.cursor/rules/<skill-name>.mdc` that points Cursor at it:
   ```markdown
   ---
   description: <paste the skill's description from manifest.json>
   globs:
   alwaysApply: false
   ---
   Follow the instructions in .cursor/skills/<skill-name>/SKILL.md when the user requests this task.
   ```

3. In chat, attach `SKILL.md` with `@` or describe the task; the rule fires when the description matches.

## Kiro (IDE and CLI)

Kiro has native **Agent Skills**, and Kiro IDE and Kiro CLI read the same directories. Copying the folder in is the whole install:

```bash
mkdir -p .kiro/skills                  # workspace scope
cp -R packs/solution-architect/skills/figma-diagrams .kiro/skills/

mkdir -p ~/.kiro/skills                # global scope, every project
cp -R packs/solution-architect/skills/figma-diagrams ~/.kiro/skills/
```

Kiro matches the skill by its `SKILL.md` frontmatter `name` (which must equal the folder name) and `description`, the same contract every other tool uses.

**No steering file needed.** Earlier versions of the CLI also wrote `.kiro/steering/<skill-name>.md` pointing back at the skill. That predates native Agent Skills, and because a steering file without frontmatter is *always* loaded, it pinned one description per installed skill into every session's context, to point at a folder Kiro already reads. The CLI no longer writes them, and `install`/`uninstall` remove any it wrote before. A steering file it didn't author is left alone, with a note.

## Codex, Antigravity and GitHub Copilot

Each has its own flag. Without `--project` the skills go to your personal folder and work in every repo; with it, they go into the repo:

```bash
npx skilldrop-cli install --pack dev-team --ide codex              # ~/.codex/skills
npx skilldrop-cli install --pack dev-team --ide antigravity        # ~/.gemini/antigravity-cli/skills
npx skilldrop-cli install --pack dev-team --ide copilot            # ~/.copilot/skills
npx skilldrop-cli install --pack dev-team --ide copilot --project  # .github/skills
npx skilldrop-cli install --pack dev-team --ide codex --project    # .agents/skills
```

All three also read other tools' folders, so a project install often reaches more than one:

| Path | Read by |
|---|---|
| `.claude/skills/` | Claude Code, **Copilot CLI** |
| `.agents/skills/` | **Codex**, **Antigravity**, **Copilot CLI** (`--ide codex --project` or `--ide antigravity --project`) |
| `.github/skills/` | **Copilot** |
| `~/.codex/skills/` | Codex (personal) |
| `~/.gemini/antigravity-cli/skills/` | Antigravity CLI (personal) |
| `~/.copilot/skills/` | Copilot (personal) |

**If you already ran `skilldrop install --project`, Copilot CLI can use every skill you installed**, because `.claude/skills/` is one of its discovery paths. Codex and Copilot also read a repo-root `AGENTS.md`. Google retired Gemini CLI for most users on 2026-06-18; Antigravity CLI replaced it, and `--ide antigravity` is its target.

## Local installs in a repo you don't own

`--local` installs into the repo (the same place `--project` would) and lists every file it writes in the repo's own `.git/info/exclude`. Git ignores those files the way it ignores `.gitignore` entries, but the exclude file is never committed, so `git status` stays clean and nothing can be committed by accident:

```bash
npx skilldrop-cli install --pack dev-team --local
npx skilldrop-cli uninstall pre-merge-review --local   # removes the files and the exclude entries
```

It works with every `--ide`. With `--with-hooks` on Claude Code, the session-start hook goes into `.claude/settings.local.json` rather than the shared `settings.json`.

## Continue, Cline, Aider, and other agents

These tools don't have a standard skills directory yet. Two patterns work:

- **Context attachment.** Copy the skill folder anywhere in the repo, then attach `SKILL.md` to your prompt (Continue: `@file`, Cline: `@file`, Aider: `/add <path>`) and tell the agent to follow it.
- **Custom prompt or agent.** Paste `SKILL.md` into the IDE's custom-agent or system-prompt configuration. The `description` field in the skill's `manifest.json` is a good seed for the agent's name and summary.

In every case the scripts run from the **copied** folder, so keep the directory structure intact: don't flatten `scripts/` or `templates/` out of the skill folder.

### VS Code (Continue and Cline extensions)

These behave like the other-agents path above. For Continue, you can also add the skill folder to `.continue/config.json` under `contextProviders` so `SKILL.md` shows up in `@` suggestions.

## Subagent targets

`--agent` installs reviewer subagents. Six targets, each projecting only as much as the tool's format demands:

| Target | Writes | Projection |
|---|---|---|
| *(default)* | `~/.claude/agents/<name>.md` | none: the file already is Claude Code's format |
| `--ide copilot` | `.github/agents/<name>.agent.md` | a rename |
| `--ide kiro` | `.kiro/agents/<name>.json` | generated JSON; tool names mapped to Kiro's built-ins |
| `--ide codex` | `~/.codex/agents/<name>.toml` (`--project` for repo) | generated TOML |
| `--ide antigravity` | `~/.gemini/config/agents/<name>.md` (`--project` → `.agents/agents/`) | frontmatter rewritten, `subagent: true` added |
| `--dest <dir>` | `<dir>/<name>.md` | none |

The Kiro emitter maps `Read`/`Grep`/`Glob`/`Bash` to `read`/`grep`/`glob`/`shell` against [Kiro's built-in tool reference](https://kiro.dev/docs/cli/reference/built-in-tools/), and **names any tool it can't map instead of dropping it silently**: a mistranslated permission is worse than a missing one.

Each generated target omits the permission field it cannot map safely rather than guessing one: Kiro's `allowedTools` and Codex's `sandbox_mode` are both left unset, so an agent inherits the session's permissions and is prompted per call. A widened permission nobody asked for is worse than an extra prompt.

**Every surveyed tool now installs.** Only Cursor is absent, because it has no agent file format at all; use a custom mode ([`agents/README.md`](../../agents/README.md) has the steps).

## Installing dependencies

Each skill declares its deps in `manifest.json`:

- **`deps.npm`**: run `npm install <packages>` before using the skill (or let `SKILL.md` step 1 install them on demand).
- **`deps.pip`**: run `python3 -m pip install -r <skill>/requirements.txt`.

Per-skill quick reference:

| Skill | Install command (run from inside the copied skill folder) |
|---|---|
| `figma-diagrams` | `python3 -m pip install -r requirements.txt` (installs `requests`) + `export FIGMA_TOKEN=figd_...` |
| `deck-builder` | `python3 -m pip install -r requirements.txt` (installs `python-pptx`) |
| _all other skills_ | _no runtime deps: pure markdown skills_ |

For `figma-diagrams`, you also need a [Figma Personal Access Token](https://www.figma.com/developers/api#access-tokens) exported as the `FIGMA_TOKEN` env var. What each skill's scripts need beyond packages is on [Skills that ship scripts](skills-with-scripts.md).
