---
title: Install a skill into your IDE
summary: Per-IDE install steps for every target skilldrop supports, plus the dependency install for the two skills that have Python deps.
kind: how-to
---

# Install a skill into your IDE

#### Manual install

Each skill is a plain directory. Installation is always the same two steps: (1) copy the skill folder into your IDE's skills/rules location, then (2) install the skill's dependencies (the commands are in `manifest.json` under `deps`, or run the install line from the skill's SKILL.md). Optionally, also copy the companions listed under `related` in the skill's `manifest.json` — skills reference each other, and while a hand-off to an uninstalled sibling degrades gracefully to inline guidance, the pipelines work best complete.

#### Claude Code

Claude Code reads skills from two locations:

- **User-scope** (available in every project): `~/.claude/skills/<skill-name>/`
- **Project-scope** (tracked with the repo): `<project>/.claude/skills/<skill-name>/`

Install a skill by copying its folder — drop the directory directly into the skills location, **not** its parent category folder:

```bash
# user-scope (recommended for personal use)
mkdir -p ~/.claude/skills
cp -R skills/architecture-diagrams ~/.claude/skills/
cp -R skills/figma-diagrams ~/.claude/skills/

# project-scope (recommended when sharing with a team)
mkdir -p .claude/skills
cp -R skills/architecture-diagrams .claude/skills/
cp -R skills/figma-diagrams .claude/skills/
```

Claude Code discovers the skill via its `SKILL.md` frontmatter `name` field. Invoke it in chat with `/<skill-name>` or by describing the task — Claude will route to the matching skill automatically.

#### Cursor

Cursor does not have a native "skills" concept, but you can install a skill as a **project rule**:

1. Copy the skill folder somewhere in the repo (e.g. `.cursor/skills/<skill-name>/`):
   ```bash
   mkdir -p .cursor/skills
   cp -R skills/architecture-diagrams .cursor/skills/
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

3. In chat, attach `SKILL.md` with `@` or simply describe the task — the rule will fire when the description matches.

#### Kiro (IDE and CLI)

Kiro has native **Agent Skills**, and Kiro IDE and Kiro CLI read the same directories. Copy the folder in — that's the whole install:

```bash
mkdir -p .kiro/skills                  # workspace scope
cp -R skills/figma-diagrams .kiro/skills/

mkdir -p ~/.kiro/skills                # global scope, every project
cp -R skills/figma-diagrams ~/.kiro/skills/
```

Kiro matches the skill by its `SKILL.md` frontmatter `name` (which must equal the folder name) and `description` — the same contract every other tool uses.

**No steering file needed.** Earlier versions of the CLI also wrote `.kiro/steering/<skill-name>.md` pointing back at the skill. That predates native Agent Skills, and because a steering file without frontmatter is *always* loaded, it pinned one description per installed skill into every session's context — to point at a folder Kiro already reads. The CLI no longer writes them, and `install`/`uninstall` remove any it wrote before. A steering file it didn't author is left alone, with a note.

#### Codex and GitHub Copilot

Both read `SKILL.md` folders, and both deliberately read *other* tools' directories — so a skilldrop install often already works with no extra step:

| Path | Read by |
|---|---|
| `.claude/skills/` | Claude Code, **Copilot CLI** |
| `.agents/skills/` | **Codex** (project), **Copilot CLI** |
| `.github/skills/` | **Copilot** |
| `~/.codex/skills/` | Codex (personal) |
| `~/.copilot/skills/` | Copilot (personal) |

**If you already ran `skilldrop install --project`, Copilot CLI can use every skill you installed** — `.claude/skills/` is one of its discovery paths. Otherwise pick the path your tool reads:

```bash
npx skilldrop-cli install --pack dev-team --dest .agents/skills    # Codex + Copilot CLI
npx skilldrop-cli install --pack dev-team --dest .github/skills    # Copilot
npx skilldrop-cli install --pack dev-team --dest ~/.codex/skills   # Codex, all projects
```

There is no `--ide codex` or `--ide copilot` flag yet, and `--dest` is not a workaround here — it writes the identical folder the native flags would. Both tools also read a repo-root `AGENTS.md`, which this repo has.

#### Continue, Cline, Aider, and other agents

These tools don't have a standard skills directory yet. Two patterns work:

- **Context attachment.** Copy the skill folder anywhere in the repo, then attach `SKILL.md` to your prompt (Continue: `@file`, Cline: `@file`, Aider: `/add <path>`) and tell the agent to follow it.
- **Custom prompt / agent.** Paste `SKILL.md` into the IDE's custom-agent or system-prompt configuration. The skill's `manifest.json` `description` field is a good seed for the agent's name/summary.

In all cases, the scripts are invoked from the **copied** folder, so keep the directory structure intact — don't flatten `scripts/` or `templates/` out of the skill folder.

#### VS Code (Continue / Cline extensions)

These behave like the "Other agents" path above. For Continue, you can also add the skill folder to `.continue/config.json` under `contextProviders` so `SKILL.md` shows up in `@` suggestions.

### Installing dependencies

Each skill declares its deps in `manifest.json`:

- **`deps.npm`** → run `npm install <packages>` before using the skill (or let `SKILL.md` step 1 install them on demand).
- **`deps.pip`** → run `python3 -m pip install -r <skill>/requirements.txt`.

Per-skill quick reference:

| Skill | Install command (run from inside the copied skill folder) |
|---|---|
| `figma-diagrams` | `python3 -m pip install -r requirements.txt` + `export FIGMA_TOKEN=figd_...` |
| `deck-builder` | `python3 -m pip install -r requirements.txt` (installs `python-pptx`) |
| _all other skills_ | _no runtime deps — pure markdown skills_ |

For `figma-diagrams`, you also need a [Figma Personal Access Token](https://www.figma.com/developers/api#access-tokens) exported as the `FIGMA_TOKEN` env var.
