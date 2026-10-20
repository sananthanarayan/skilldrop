---
title: Install options
summary: Every skilldrop CLI install command and flag, the Claude Code plugin marketplace's plugins and how they are built, the reviewer subagents, and where to go for hooks, catalogues and authoring.
kind: reference
---

# Install options

The commands, flags and plugin details behind [Install skills, packs and loops](../how-to/install.md). Where each target puts files, and the dependency installs, are on [Install targets and dependencies](install-targets.md).

## The skilldrop CLI

The repo ships as the npm package **`skilldrop-cli`** (command: `skilldrop`): a zero-dependency installer that copies skills byte-identical into your tool's location, and writes a pointer file only where the tool needs one to find them (Cursor). From a clone, or before the package is published, run `node bin/skilldrop.js <same args>`. Scope and design: [RFC-0002](../../docs/rfcs/0002-skilldrop-cli.md); the full command surface is in [`docs/designs/skilldrop-cli-design.md`](../../docs/designs/skilldrop-cli-design.md).

```bash
npx skilldrop-cli install --pack product-manager        # Claude Code, user scope (~/.claude/skills)
npx skilldrop-cli install --pack dev-team --project     # .claude/skills — also read by GitHub Copilot CLI
npx skilldrop-cli install prfaq --ide cursor            # + writes .cursor/rules/prfaq.mdc
npx skilldrop-cli install --pack sre-oncall --ide kiro  # .kiro/skills — Kiro IDE + Kiro CLI, discovered natively
npx skilldrop-cli install adr-generator --dest .agents/skills   # Codex + Copilot CLI
npx skilldrop-cli loops                                 # every loop, its stages and gates
npx skilldrop-cli install --loop build                  # a loop + every stage skill it sequences (RFC-0028)
npx skilldrop-cli install --loop --pack sre-oncall      # every loop that pack declares
npx skilldrop-cli agents                                # the reviewer subagents
npx skilldrop-cli install --agent devils-advocate       # -> ~/.claude/agents/ (RFC-0012)
npx skilldrop-cli install --panel review                # the whole review fleet: 3 subagents + the pre-merge-review orchestrator (RFC-0020)
npx skilldrop-cli outdated && npx skilldrop-cli update  # skills improve; files you edited are kept, new copy as <file>.upstream
npx skilldrop-cli list | skilldrop info <skill> | skilldrop info --pack <name> | skilldrop packs | skilldrop uninstall <skill>
npx skilldrop-cli list --json                            # machine-readable: list/info/packs/agents/outdated (RFC-0021)
npx skilldrop-cli search <words> [--kind skill|loop|agent|pack] [--limit N] [--json]   # by what it's for (RFC-0056)
```

## Install flags

| Flag | Effect |
|---|---|
| `--pack <name>` | Installs a whole pack, together with the packs it requires (`core`). |
| `--all` | Installs every skill in the catalogue. |
| `--profile <name>` | Installs a named bundle of packs, agents and loops; see [Install a profile](../how-to/profiles.md). |
| `--with-related` | Also installs each skill's `related` companions, one level deep. |
| `--loop <name...>` | Installs a loop as an invokable skill (its `LOOP.md` is already `SKILL.md`-shaped) plus the skills its stages name. |
| `--no-skills` | With `--loop`: the loop alone. It still runs, because each stage degrades through its declared `fallback`. |
| `--loop --pack <name>` | Every loop a pack declares. |
| `--agent <name...>` | Reviewer subagents instead of skills; targets are in [Subagent targets](install-targets.md#subagent-targets). |
| `--panel review` | The three reviewer subagents plus the `pre-merge-review` orchestrator that fires them. |
| `--from <dir\|url>` | Installs from another catalogue; append `#<commit-sha>` to pin a git URL. See [Publish your own catalogue](../how-to/publish-a-catalogue.md). |
| `--project`, `--local`, `--ide <tool>`, `--dest <dir>` | Pick the target; see [Install targets and dependencies](install-targets.md). |
| `--with-hooks` | Also wires any hooks a skill declares; see [Wire a skill to an event](../how-to/wire-a-hook.md). |
| `--dry-run` | Prints what `install`, `update` or `uninstall` would change, and changes nothing. |
| `--json` | Machine-readable output for `list`, `search`, `info`, `packs`, `agents`, `outdated` and `doctor`. |

After the first install that succeeds at an interactive terminal, the CLI prints one line
asking for a GitHub star, and writes `~/.config/skilldrop/star-shown` so the line never shows
again. It doesn't print in CI, in a pipe or with `--json`, and nothing is sent anywhere. Set
`SKILLDROP_NO_STAR=1` to turn it off before it ever shows.

## The Claude Code plugin marketplace

skilldrop is also a **Claude Code plugin marketplace**: one marketplace with one plugin for the whole catalogue plus one per pack, and no npm step. Add it once:

```text
/plugin marketplace add sananthanarayan/skilldrop
```

Then take the whole catalogue, or your role's pack:

```text
/plugin install skilldrop@skilldrop             # all 96 skills + 3 reviewer subagents
/plugin install dev-team@skilldrop              # 20 skills (incl. core) + the 3 reviewer subagents
/plugin install solution-architect@skilldrop    # 15 skills (incl. core)
/plugin install ai-engineering@skilldrop        # 15 skills (incl. core)
/plugin install product-manager@skilldrop       # 12 skills (incl. core)
/plugin install sre-oncall@skilldrop            # 11 skills (incl. core)
/plugin install core@skilldrop                  # 4 skills, on their own
# …and one plugin for every other pack: run `npx skilldrop-cli packs` for the list
```

Every skill then invokes as `/<plugin>:<name>` (for example `/skilldrop:prfaq`). The whole-catalogue plugin is the repo root itself: its `plugin.json` lists each `packs/<pack>/skills/` folder, and `agents/` sits at the root. It is the same copy-install premise, expressed in Claude's own plugin format.

## How the pack plugins are built

A plugin's skills have to sit in a `skills/` folder inside the plugin, and a role pack's plugin also has to carry `core`'s skills and loops, since a plugin installs on its own and cannot reach outside its folder. Rather than copy `core` into every pack folder on `main`, the marketplace entries use Claude's `git-subdir` source to point at `packs/<name>/` on a generated [`plugins`](https://github.com/sananthanarayan/skilldrop/tree/plugins) branch. CI rebuilds that branch on every push to main, assembling each pack with `core` folded in. You still only type the one `marketplace add`.

A pack plugin carries the reviewer subagents its own skills delegate to, so `dev-team` brings the review panel and `sre-oncall` does not.

`.claude-plugin/{marketplace,plugin}.json` are generated from `package.json` and the `packs/` folders by [`build_marketplace.py`](../../build_marketplace.py): `--check` guards drift in CI, and `--dist` renders the branch. Rationale: [RFC-0027](../../docs/rfcs/0027-retire-agentbundle-export.md).

## CLI or marketplace

| Use | When you want |
|---|---|
| The CLI | per-skill granularity, another IDE, or hooks |
| The marketplace | to stay inside Claude Code |

## Reviewer subagents

Three personas you delegate review to, rather than invoke as a skill: [`devils-advocate`](../../agents/devils-advocate.md) ("will this break?"), [`code-quality`](../../agents/code-quality.md) ("will the next engineer hate this?") and [`security-reviewer`](../../agents/security-reviewer.md) ("how would someone abuse this?"). A subagent runs in its own context with its own tool allowlist, a contract a skill can't express, which is why they live in [`agents/`](../../agents) instead of a pack's `skills/`.

```bash
npx skilldrop-cli agents                                    # list them
npx skilldrop-cli install --agent devils-advocate           # ~/.claude/agents/
npx skilldrop-cli install --agent code-quality --project    # .claude/agents/, shared with the repo
```

Then delegate by name: *"use the devils-advocate agent on this diff."* Where each tool's subagents land is in [Subagent targets](install-targets.md#subagent-targets).

## Related pages

- Install by hand into a specific IDE: [Install a skill into your IDE](../how-to/install-per-ide.md)
- Wire a skill to an event (opt-in hooks): [Wire a skill to an event](../how-to/wire-a-hook.md)
- Publish your own catalogue for `--from`: [Publish your own catalogue](../how-to/publish-a-catalogue.md)
- Check what a skill's scripts need: [Skills that ship scripts](skills-with-scripts.md)
- Add a skill or a loop to this repo: [Author a skill](../how-to/author-a-skill.md) · [Author a loop](../how-to/author-a-loop.md)
- Understand why it is built this way: [Why loops](../explanation/loops.md) · [ARCHITECTURE.md](../../ARCHITECTURE.md)
- See one change go through the loops: [Follow one change through the loops](../tutorial/follow-a-change-through-the-loops.md)
- Point a model at this repo: [`llms.txt`](../../llms.txt), a generated index so a tool reads the few relevant pages instead of the tree
