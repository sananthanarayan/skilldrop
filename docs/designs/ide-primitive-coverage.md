# IDE primitive coverage — running survey

**Purpose:** track what each target tool supports across the four agent primitives (skills, subagents, hooks, slash commands) and where skilldrop's coverage stops. Written iteratively; each pass takes one tool or one primitive and appends findings so later passes don't repeat work.

**Status:** in progress. Started 2026-07-26.

## What skilldrop ships today

| Primitive | Where it lives | Install path |
|---|---|---|
| Skills (49) | `skills/<name>/` — `SKILL.md` + `manifest.json` | `cp -R`, `pack.py`, or `skilldrop install` |
| Subagents (2) | `agents/devils-advocate.md`, `agents/code-quality.md` — Claude Code frontmatter + portable body. Plus `.claude/agents/model-router.md` (repo-internal) | **Manual copy only** — the CLI does not install agents |
| Hooks | Neutral `hooks` array in `manifest.json`; vocabulary `session-start`, `pre-commit-review`, `on-demand` (RFC-0006) | `skilldrop install --with-hooks` → Claude Code `settings.json` + `.git/hooks/pre-commit` |
| Slash commands | **None.** Skills are invoked as `/<skill-name>` where the tool derives commands from skills; skilldrop ships no first-class command files | n/a |

**CLI install targets** (`bin/skilldrop.js`): `claude` (default), `cursor`, `kiro`, plus `--dest <dir>` as the escape hatch. `--ide` rejects anything else.

## Per-tool status

Legend: ✅ shipped · 🟧 partial / manual · ❌ no support in skilldrop · — tool has no such primitive

| Tool | Skills | Subagents | Hooks | Slash commands |
|---|---|---|---|---|
| Claude Code | ✅ `--ide claude` | 🟧 manual copy to `.claude/agents/` | ✅ `session-start`, `pre-commit-review` | 🟧 derived from skills |
| Cursor | ✅ `--ide cursor` (+ `.cursor/rules/*.mdc`, `alwaysApply: false`) | 🟧 manual (custom mode / rule) | ❌ skipped by design (no hook system as of RFC-0006) | 🟧 derived |
| Kiro IDE | ✅ `--ide kiro` → `.kiro/skills/` (now the **native** path) — but the steering shim is stale, see iteration 2 | 🟧 manual; native `.kiro/agents/*.json` exists | 🟧 native hooks not emitted; `preToolUse` is a real target | 🟧 derived |
| **OpenAI Codex** | ❌ no `--ide codex` | ❌ | ❌ deferred in RFC-0006 | ❌ |
| **Kiro CLI** | ❌ no `--ide` target; shares Kiro's paths | ❌ `.kiro/agents/*.json` not emitted | 🟧 same as Kiro IDE | 🟧 derived |
| **GitHub Copilot** | 🟧 **already works unintentionally** — Copilot CLI reads `.claude/skills/`, which `--project` writes | ❌ `.github/agents/*.agent.md` not emitted | ❌ `.github/hooks/*.json` — has a real `sessionStart` **and** `preToolUse` | ❌ `.github/prompts/*.prompt.md` — first authorable slash-command format found |
| Gemini CLI | *not yet surveyed* | | | |

---

## Iteration log

### Iteration 1 — OpenAI Codex (2026-07-26)

**Finding: RFC-0006's deferral of Codex is stale, and the CLI gap is now the bigger one.**

RFC-0006 deferred Codex hooks on the grounds that "its mechanism is thinner than a full hook model." That was accurate when written. As of 2026 Codex CLI ships all four primitives:

| Primitive | Codex support | Verified? |
|---|---|---|
| Skills | `SKILL.md` with YAML frontmatter (`name`, `description`); `/skills` is a built-in command | Format confirmed; **exact install directory not yet confirmed** |
| Subagents | Shipped 2026-04-23 with GPT-5.5; multi-agent orchestration via `.toml` agent definitions under `.codex/` | Confirmed at directory level; **exact filename/schema not confirmed** |
| Hooks | `.codex/hooks.toml`, `[[hooks]]` entries with `event` / `command` / `description`; events `pre-commit`, `post-edit`, `pre-push`, `pre-spawn` (beta) | **Confirmed** — path, format, and event names |
| Slash commands | 29 built-ins incl. `/plan`, `/skills`, `/review`, `/fork`, `/fast` | Confirmed as built-ins; **custom-command format not confirmed** |
| `AGENTS.md` | Read natively | Confirmed |

**Why this matters more than the hooks question:** skilldrop's `SKILL.md` + `manifest.json` folder is *already* the shape Codex reads. The blocker isn't format translation — it's that `skilldrop install --ide codex` errors out, so every Codex user is pushed to `--dest` and has to know the target path themselves. That is the cheapest, highest-leverage gap on this list.

**Hooks mapping is unusually clean too.** `.codex/hooks.toml` maps to skilldrop's neutral vocabulary with almost no impedance:

| skilldrop event | Codex event | Note |
|---|---|---|
| `pre-commit-review` | `pre-commit` | Near-exact match — better than the git-hook fallback skilldrop emits today |
| `session-start` | *(none)* | No session-lifecycle event; degrades to skip per RFC-0006's contract |
| `on-demand` | *(none)* | Covered by `/skills` invocation instead |

Codex also has `post-edit` and `pre-push`, which skilldrop's vocabulary cannot express. **Do not widen the vocabulary to match** — RFC-0006's whole position is graceful degradation over parity, and adding events because one tool has them inverts that.

**Recommendation (not yet built, per instruction):**

1. **Add `--ide codex` to the CLI** — the single highest-value item found so far. Needs the exact skills directory confirmed first (`.codex/skills/` is the likely convention but is **unverified**; do not ship on a guess — that is the invented-path failure mode `agents-md-generator` exists to prevent).
2. **Map `pre-commit-review` → `.codex/hooks.toml`** once (1) lands. Small, and it replaces a generic git hook with a native one.
3. **Do not** add `post-edit` / `pre-push` to the neutral vocabulary.
4. **Open question for the owner:** subagents are a real second gap — `agents/` is manual-copy for *every* tool, including Claude Code. Codex now having a native `.toml` agent format makes "should the CLI install subagents too?" a live question. That is RFC-shaped and larger than a target addition.

**Sources:** [Codex CLI complete reference 2026](https://www.codegateway.dev/en/blog/openai-codex-cli-complete-guide-2026) · [Codex CLI in 2026: what's new](https://codex.danielvaughan.com/2026/03/27/codex-cli-in-2026-whats-new/) · [awesome-codex-cli](https://github.com/RoggeOhta/awesome-codex-cli) · [Codex CLI cheat sheet](https://toolsbase.dev/en/reference/codex-commands)

**Next iteration:** Kiro CLI (distinct from Kiro IDE, which the CLI already targets) — or confirm Codex's skills directory from a primary source before recommending (1) be built.

**Codex path follow-up (iteration 2):** multiple secondary sources agree on `~/.codex/skills/` (personal) and `.codex/skills/` (project); one instead shows `.agents/skills/` for the committed project case. **Still not confirmed against OpenAI's own docs, and the sources conflict** — the recommendation to build `--ide codex` stays blocked on a primary source.

### Iteration 2 — Kiro CLI, and a defect in the existing Kiro target (2026-07-26)

Kiro CLI and Kiro IDE **share configuration paths** — this is one target, not two. Confirmed against [kiro.dev](https://kiro.dev/docs/skills/) (primary source):

| Primitive | Kiro path | Format |
|---|---|---|
| Skills | `.kiro/skills/` (workspace), `~/.kiro/skills/` (global) | `SKILL.md` + YAML frontmatter; `name` must match the folder name, lowercase/hyphens, ≤64 chars; `description` ≤1024 chars |
| Custom agents | `.kiro/agents/*.json` (local), `~/.kiro/agents/*.json` (global) | JSON; **filename minus `.json` = agent name**. Fields: `name`, `description`, `prompt` (inline **or `file://` URI**), `mcpServers`, `tools`, `allowedTools`, `resources`, `hooks`, `model` |
| Hooks | Per-agent `hooks` field, plus IDE file-event hooks | Agent lifecycle events: `userPromptSubmit`, `preToolUse` (**can block the tool call**), `postToolUse`, `stop` |
| Slash commands | Built-in set incl. `/agent generate` | Not user-authorable as files |

**Finding 1 — the `--ide kiro` steering shim is now stale, and it is a context leak.**

Kiro shipped native Agent Skills on 2026-02-05. skilldrop's CLI already copies skill folders to `.kiro/skills/`, which is **exactly the path Kiro now discovers natively** — so the skill works on its own. On top of that, `writeWiring()` in `bin/skilldrop.js` also writes `.kiro/steering/<skill>.md` containing a "defer to `.kiro/skills/<skill>/SKILL.md`" pointer plus the description.

That shim predates native skills. Two problems now:

- **Redundant** — it points at a folder Kiro already reads.
- **Unbounded context cost** — compare the two branches of `writeWiring()`. The Cursor branch writes `alwaysApply: false`, so the rule is inert until matched. The Kiro branch writes **no frontmatter at all**, and a Kiro steering file with no inclusion mode defaults to always-included. Install a pack of 15 skills and 15 descriptions are pinned into every Kiro session's context, permanently, to point at skills Kiro would have found anyway.

Cursor's shim is still justified — `.cursor/skills/` is not a native discovery path, so the `.mdc` rule is what makes the skill reachable. Kiro's no longer is.

**Finding 2 — Kiro custom agents are the first native home for `agents/`.**

`agents/devils-advocate.md` and `agents/code-quality.md` are manual-copy everywhere today. Kiro's agent JSON has a `prompt` field that accepts a **`file://` URI** — so a generated `.kiro/agents/devils-advocate.json` could point straight at the installed markdown body instead of duplicating it. That is the cleanest subagent projection available on any surveyed tool, and it strengthens the iteration-1 question of whether the CLI should install subagents at all.

**Finding 3 — `preToolUse` is a better `pre-commit-review` target than the git hook.**

RFC-0006 mapped Kiro's `pre-commit-review` to "manual/on-demand agent hook" and fell back to `.git/hooks/pre-commit`. Kiro's `preToolUse` **can block a tool call**, so a hook matching the git-commit tool is a genuine blocking gate — the thing RFC-0006's decision section explicitly left as "a user edit". `session-start` still has no Kiro equivalent (`userPromptSubmit` fires per message, not per session) and should keep degrading to skip.

**Recommendation (not built, per instruction) — ranked:**

1. **Drop the Kiro steering shim** (or gate it behind a flag). Smallest change, fixes a live context leak, and it is a *fix to existing behavior* — no RFC needed under the current rule. Verify first that a fresh Kiro workspace discovers `.kiro/skills/` with no steering file present.
2. **`--ide codex`** — still the highest-value *addition*, still blocked on confirming the path from a primary source.
3. **Subagent installation as a CLI primitive** — RFC-shaped. Kiro (`file://` JSON) and Codex (`.toml`) both have native formats now; Claude Code's `.claude/agents/` is a plain copy. Three real targets is enough to justify the design.
4. **`preToolUse` mapping for `pre-commit-review`** — do after (3), since both touch the same projection layer.

**Sources:** [Kiro Agent Skills docs](https://kiro.dev/docs/skills/) · [Kiro CLI agent configuration reference](https://kiro.dev/docs/cli/custom-agents/configuration-reference/) · [Kiro 0.9 changelog — custom subagents, agent skills, new hook triggers](https://kiro.dev/changelog/ide/0-9/) · [Kiro CLI](https://kiro.dev/cli/) · [Steering vs AgentSkills](https://dev.to/aws-builders/aws-differences-between-kiro-steering-and-agentskills-kiro-5f3i) · Codex paths: [where Codex CLI skills are stored](https://www.agensi.io/learn/where-are-codex-cli-skills-stored) · [installing SKILL.md in Codex CLI](https://www.mdskills.ai/learn/how-to-install-skills-codex-cli)

**Next iteration:** GitHub Copilot (skills/instructions, custom agents, and whether it has any hook surface) — or Gemini CLI.

### Iteration 3 — GitHub Copilot, and the finding that reframes the whole survey (2026-07-26)

Copilot is the first surveyed tool with a **native file home for all four primitives**:

| Primitive | Copilot path | Format |
|---|---|---|
| Skills | `.github/skills/<name>/SKILL.md` (repo), `~/.copilot/skills/` (user). Copilot CLI **also reads `.claude/skills/` and `.agents/skills/`** | `SKILL.md`; frontmatter `name`, `description`, optional `license`, `allowed-tools` |
| Custom agents | `.github/agents/<name>.agent.md` (repo), `~/.copilot/agents/` (user) | Frontmatter `name`, `description`, `tools`, `disable-model-invocation`, `user-invocable`, `mcp-servers`. **Filename minus `.agent.md` is the invocation name** — `copilot --agent security-auditor` |
| Hooks | `.github/hooks/*.json` | Events: `sessionStart`, `sessionEnd`, `userPromptSubmitted`, `preToolUse`, `postToolUse`, `agentStop`, `subagentStop`, `errorOccurred` |
| Slash commands | `.github/prompts/<name>.prompt.md` | Reusable task templates invoked explicitly in chat — **the first user-authorable slash-command format found in this survey** |
| Instructions | `.github/copilot-instructions.md`, root `AGENTS.md`, `.github/instructions/*.instructions.md` | Also reads root `CLAUDE.md` and `GEMINI.md` |

**Finding 1 — skilldrop already supports Copilot CLI by accident.** `skilldrop install --project` writes `.claude/skills/<name>/`, and Copilot CLI reads that path. Any Copilot CLI user can already install every skilldrop skill today; nothing in the README says so. **Cheapest win in the whole survey: a documentation change, not a code change.**

**Finding 2 — `.agents/skills/` is a shared convention, and it resolves iteration 2's open conflict.** The `.agents/skills/` path that looked like a contradictory Codex source is not an error — it is Codex's *project-scope* convention, distinct from its personal `~/.codex/skills/`. Copilot CLI reads it too. So:

| Path | Read by |
|---|---|
| `.agents/skills/` | Codex (project), Copilot CLI |
| `.claude/skills/` | Claude Code, Copilot CLI |
| `.github/skills/` | Copilot |
| `.kiro/skills/` | Kiro IDE + Kiro CLI |
| `~/.codex/skills/` | Codex (personal) |
| `~/.copilot/skills/` | Copilot (personal) |

**This reframes the CLI question.** The plan implied by iterations 1–2 — add `--ide codex`, then `--ide copilot`, then `--ide gemini`, one target at a time — is the wrong shape. The formats are already identical (`SKILL.md` + folder); only the *directory* differs, and several tools deliberately read each other's. A `--ide <tool>` flag per tool is N flags maintaining a lookup table that is mostly one of six strings.

Worth noting as prior art: at least one existing multi-agent installer symlinks each tool's expected directory to a single canonical copy. **skilldrop should not copy that** — symlinks break the plain-copy portability premise and behave badly on Windows — but the underlying observation (one canonical copy, many discovery paths) is the right one.

**Finding 3 — Copilot is the second real `session-start` target, and the first slash-command target.** RFC-0006's vocabulary maps cleanly: `session-start` → `sessionStart`, `pre-commit-review` → `preToolUse` (blocking, matched on the git-commit tool). No vocabulary widening needed — the neutral events land as-is, which is the strongest evidence so far that RFC-0006's degradation contract was designed right.

Slash commands are the genuinely **new** primitive. skilldrop ships none; `.github/prompts/*.prompt.md` is the first format that is user-authorable as a file. Whether skilldrop should generate one per skill is an open design question, not an obvious yes — a `/skill-name` prompt file that just says "read `SKILL.md`" is the same redundancy as the Kiro steering shim from iteration 2.

**Recommendation (not built, per instruction) — revised ranking across all three iterations:**

1. **Document that Copilot CLI and Codex already work** via `.claude/skills/` and `.agents/skills/`. Zero code. README + `AGENTS.md` install table.
2. **Drop the Kiro steering shim** (iteration 2, finding 1) — still a live context leak.
3. **Replace the `--ide <tool>` design with a path-set model** before adding any more targets. One canonical copy, a table of discovery paths per tool, `--ide` kept as an alias that resolves to a path. This is RFC-shaped and it should land *before* `--ide codex`, `--ide copilot`, or `--ide gemini` — otherwise three more flags get written against a design already known to be wrong.
4. **Subagent installation** (iteration 2, finding 2) — now four native targets: Kiro JSON (`file://`), Codex `.toml`, Copilot `.agent.md`, Claude Code plain copy. Same RFC as (3) or its immediate sequel.
5. **Hooks: add Copilot's `.github/hooks/*.json`** — `session-start` and `pre-commit-review` both map natively. After (3).
6. **Slash commands: open question, do not build yet.** Needs a reason to exist beyond mirroring skills.

**Sources:** [VS Code Copilot customization overview](https://code.visualstudio.com/docs/copilot/customization/overview) · [Copilot CLI custom agents and skills](https://www.devleader.ca/2026/07/23/github-copilot-cli-custom-agents-and-skills) · [About agent skills — GitHub Docs](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) · [Mastering Copilot customization: instructions, skills, prompt files, agents, hooks](https://anaops.wordpress.com/2026/07/06/mastering-github-copilot-customization-from-copilot-instructions-to-skills-prompt-files-agents-and-hooks/) · [github/awesome-copilot agents docs](https://github.com/github/awesome-copilot/blob/main/docs/README.agents.md) · [Agent skills side-by-side: Claude Code, Copilot, Codex, Cursor](https://blog.ainative.medhavi.dev/p/set-up-agent-skills-in-claude-code-copilot-codex-cursor-a-side-by-side-guide)

**Next iteration:** Gemini CLI — the last unsurveyed tool. After that the survey is complete and the open item is the path-set RFC.
