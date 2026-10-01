---
title: Install skills, packs and loops
summary: Every install route — the skilldrop CLI (any IDE), the Claude Code plugin marketplace, and by hand — with the flags each one takes.
kind: how-to
---

# Install skills, packs and loops


## Quickest: the skilldrop CLI

The repo ships as the npm package **`skilldrop-cli`** (command: `skilldrop`) — a zero-dependency installer that copies skills byte-identical into your tool's location, and writes a pointer file only where the tool needs one to find them (Cursor):

```bash
npx skilldrop-cli install --pack product-manager        # Claude Code, user scope (~/.claude/skills)
npx skilldrop-cli install --pack dev-team --project     # .claude/skills — also read by GitHub Copilot CLI
npx skilldrop-cli install prfaq --ide cursor            # + writes .cursor/rules/prfaq.mdc
npx skilldrop-cli install --pack sre-oncall --ide kiro  # .kiro/skills — Kiro IDE + Kiro CLI, discovered natively
npx skilldrop-cli install adr-generator --dest .agents/skills   # Codex + Copilot CLI (see below)
npx skilldrop-cli loops                                 # the six loops, their stages and gates
npx skilldrop-cli install --loop build                  # a loop + every stage skill it sequences (RFC-0028)
npx skilldrop-cli install --loop --pack sre-oncall      # every loop that pack declares
npx skilldrop-cli agents                                # the reviewer subagents
npx skilldrop-cli install --agent devils-advocate       # -> ~/.claude/agents/ (RFC-0012)
npx skilldrop-cli install --panel review                # the whole review fleet: 3 subagents + the pre-merge-review orchestrator (RFC-0020)
npx skilldrop-cli outdated && npx skilldrop-cli update  # skills improve; files you edited are kept, new copy as <file>.upstream
npx skilldrop-cli list | skilldrop info <skill> | skilldrop info --pack <name> | skilldrop packs | skilldrop uninstall <skill>
npx skilldrop-cli list --json                            # machine-readable: list/info/packs/agents/outdated (RFC-0021)
```

`--loop` installs a loop as an invokable skill (its `LOOP.md` is already `SKILL.md`-shaped) plus the skills its stages name — add `--no-skills` for the loop alone, which still runs because each stage degrades through its declared `fallback`. `--with-related` also pulls each skill's companions. From a clone (or before the package is published): `node bin/skilldrop.js <same args>`. Scope and design: [RFC-0002](../../docs/rfcs/0002-skilldrop-cli.md), full command surface in [`docs/designs/skilldrop-cli-design.md`](../../docs/designs/skilldrop-cli-design.md).

## Or: the Claude Code plugin marketplace

skilldrop is also a **Claude Code plugin marketplace** — one marketplace, nine plugins (the whole catalogue, plus one per pack), no npm step. Add it once:

```text
/plugin marketplace add sananthanarayan/skilldrop
```

Then take the whole catalogue, or just your role's pack:

```text
/plugin install skilldrop@skilldrop             # all 63 skills + 3 reviewer subagents
/plugin install dev-team@skilldrop              # 18 skills (incl. core) + the 3 reviewer subagents
/plugin install solution-architect@skilldrop    # 15 skills (incl. core)
/plugin install ai-engineering@skilldrop        # 15 skills (incl. core)
/plugin install product-manager@skilldrop       # 12 skills (incl. core)
/plugin install stakeholder-comms@skilldrop     # 10 skills (incl. core)
/plugin install sre-oncall@skilldrop            # 9 skills (incl. core)
/plugin install claude-api@skilldrop            # 4 skills
/plugin install core@skilldrop                  # 4 skills, on their own
```

Every skill then invokes as `/<plugin>:<name>` (e.g. `/skilldrop:prfaq`). The whole-catalogue plugin is the repo root itself: its `plugin.json` lists each `packs/<pack>/skills/` folder, and `agents/` sits at the root — same copy-install premise, expressed in Claude's own plugin format.

The eight **pack plugins** work differently, because a plugin's skills have to sit in a `skills/` folder inside the plugin. A role pack's plugin also has to carry `core`'s skills and loops, since a plugin installs on its own and cannot reach outside its folder. Rather than copy `core` into every pack folder on `main`, the marketplace entries use Claude's `git-subdir` source to point at `packs/<name>/` on a generated [`plugins`](https://github.com/sananthanarayan/skilldrop/tree/plugins) branch, rebuilt by CI on every push to main, where each pack is assembled with `core` folded in. You still only ever type the one `marketplace add`. A pack carries the reviewer subagents its own skills delegate to, so `dev-team` brings the review panel and `sre-oncall` does not.

`.claude-plugin/{marketplace,plugin}.json` are generated from `package.json` + the `packs/` folders by [`build_marketplace.py`](../../build_marketplace.py) (`--check` guards drift in CI; `--dist` renders the branch). Use the CLI above when you want per-skill granularity, another IDE, or hooks; use the marketplace when you're in Claude Code. Rationale: [RFC-0027](../../docs/rfcs/0027-retire-agentbundle-export.md).

## Everything else about installing

The long-form install material moved to [`guides/`](..) so this page stays scannable:

| If you want to | Read |
|---|---|
| Install by hand into a specific IDE | [Install a skill into your IDE](../how-to/install-per-ide.md) |
| Wire a skill to an event (opt-in hooks) | [Wire a skill to an event](../how-to/wire-a-hook.md) |
| Publish your own catalogue for `--from` | [Publish your own catalogue](../how-to/publish-a-catalogue.md) |
| Use the two skills that ship scripts | [Skills that ship scripts](../reference/skills-with-scripts.md) |
| Add a skill or a loop to this repo | [Author a skill](../how-to/author-a-skill.md) · [Author a loop](../how-to/author-a-loop.md) |
| Understand why it is built this way | [Why loops](../explanation/loops.md) · [ARCHITECTURE.md](../../ARCHITECTURE.md) |
| See one change go through the loops | [Follow one change through the loops](../tutorial/follow-a-change-through-the-loops.md) |
| Point a model at this repo | [`llms.txt`](../../llms.txt) — a generated index so a tool reads the few relevant pages instead of the tree |

## Reviewer subagents

Three personas you delegate review to, rather than invoke as a skill: [`devils-advocate`](../../agents/devils-advocate.md) ("will this break?"), [`code-quality`](../../agents/code-quality.md) ("will the next engineer hate this?") and [`security-reviewer`](../../agents/security-reviewer.md) ("how would someone abuse this?"). A subagent runs in its own context with its own tool allowlist — a contract a skill can't express — which is why they live in [`agents/`](../../agents) instead of a pack's `skills/`.

```bash
npx skilldrop-cli agents                                    # list them
npx skilldrop-cli install --agent devils-advocate           # ~/.claude/agents/
npx skilldrop-cli install --agent code-quality --project    # .claude/agents/, shared with the repo
```

Then delegate by name: *"use the devils-advocate agent on this diff."*

Six targets, each projecting only as much as the tool's format demands:

| Target | Writes | Projection |
|---|---|---|
| *(default)* | `~/.claude/agents/<name>.md` | none — the file already is Claude Code's format |
| `--ide copilot` | `.github/agents/<name>.agent.md` | a rename |
| `--ide kiro` | `.kiro/agents/<name>.json` | generated JSON; tool names mapped to Kiro's built-ins |
| `--ide codex` | `~/.codex/agents/<name>.toml` (`--project` for repo) | generated TOML |
| `--ide antigravity` | `~/.gemini/config/agents/<name>.md` (`--project` → `.agents/agents/`) | frontmatter rewritten, `subagent: true` added |
| `--dest <dir>` | `<dir>/<name>.md` | none |

The Kiro emitter maps `Read`/`Grep`/`Glob`/`Bash` to `read`/`grep`/`glob`/`shell` against [Kiro's built-in tool reference](https://kiro.dev/docs/cli/reference/built-in-tools/), and **names any tool it can't map instead of dropping it silently** — a mistranslated permission is worse than a missing one. It omits `allowedTools` so you're prompted per tool call.

Each generated target omits the permission field it cannot map safely rather than guessing one: Kiro's `allowedTools` and Codex's `sandbox_mode` are both left unset, so an agent inherits the session's permissions and is prompted per call. A widened permission nobody asked for is worse than an extra prompt.

**Every surveyed tool now installs.** Only Cursor is absent, because it has no agent file format at all — use a custom mode ([`agents/README.md`](../../agents/README.md) has the steps).
