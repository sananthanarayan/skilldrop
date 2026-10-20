---
name: agent-config-review
description: Review a coding agent's configuration for access broader than the work needs and give a verdict — SAFE AS CONFIGURED, TIGHTEN BEFORE USE or DO NOT USE — reading what actually wins across every scope (Claude Code user, project, local and managed settings; permission allow/deny/ask lists, defaultMode, sandbox, hooks, plugins, env; .mcp.json; subagent tool lists; Codex sandbox_mode and approval_policy and the profile in use; Cursor and Copilot agent settings), with each finding's file and line, what it lets happen in plain words, and the exact replacement config. Use when the user asks "is this Claude Code / Codex / Cursor setup safe", "review our .claude/settings.json", "audit our agent permissions", "is Bash(npm:*) OK in the allow list", "check this repo's agent config before we open it", or wants an agent's permissions tightened before use.
---

# agent-config-review

Reads the configuration a coding agent will actually run with and says whether it is safe to
use as it stands. The files lie by omission: the effective permission is what every scope adds
up to, an allow entry means what the command can do rather than what it is called, and the
settings that run shell without asking (hooks, status lines, MCP servers) sit outside the
sandbox. The output is a verdict, the findings worst first, and the config that replaces each.

It reviews an existing setup. Choosing which MCP servers a workflow should connect is
`mcp-pairing`; attacking an agent's design for data-exfiltration paths is `agent-threat-model`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** The verdict is the worst finding's, and it covers only the files read: name each scope not seen. A secret found in a committed file is rotated, not just moved.

1. **Collect every scope before judging one file.** Claude Code reads user (`~/.claude/settings.json`), project (`.claude/settings.json`), local (`.claude/settings.local.json`) and managed policy, plus MCP servers from `.mcp.json`, `~/.claude.json` and plugins. Codex reads `~/.codex/config.toml` and the profile it is launched with. Locations for every tool are in [`reference.md`](reference.md). Spend at most 2 questions, on how the agent is launched (flags, profile) and what work it is for; otherwise tag both `[assumption]`.

2. **List what the files grant, mechanically.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/agent_config_scan.py" <project-dir> [--user <home>] [--managed <file>] [--also <file> ...]
   # Other IDEs (from the skill folder)
   python3 scripts/agent_config_scan.py <project-dir> [--user <home>] [--managed <file>] [--also <file> ...]
   ```

   It merges the scopes, prints effective rules, sandbox, hooks, MCP servers, subagents, Codex
   profiles and masked secrets with file:line, and lists patterns to grade. Pass any token or
   env file a config references with `--also`. If no script can run, do the merge in step 3 by
   hand. The script lists; the grading is yours.

3. **Judge what wins, not what one file says.** In Claude Code, `allow`/`ask`/`deny` lists **add up** across scopes and a deny anywhere beats an allow anywhere; a single value (`defaultMode`) comes from the highest scope that sets it: managed > command-line flags > local > project > user. The local file is per-person and is where a loosened mode hides.
   - ❌ *"defaultMode is acceptEdits, so edits are the only thing that skips a prompt."*
   - ✅ *"`.claude/settings.local.json:3` sets `bypassPermissions`, which outranks the project's `acceptEdits`: every tool call runs without a prompt."*
   - In Codex, the profile in use overrides the top level: review `[profiles.<name>]` for the one the user launches with.

4. **Read every allow entry as what it lets run.** An interpreter, package manager, build tool or `git`/`gh`/`docker` with a wildcard is arbitrary code. Table in [`reference.md`](reference.md).
   - ❌ *"`Bash(npm:*)` is fine, it's just npm."*
   - ✅ *"`Bash(npm:*)` runs any `package.json` script and `npm exec` downloads and runs any package. Replace with the scripts the work uses:"* `"Bash(npm run test)", "Bash(npm run lint)"`
   - `bypassPermissions`, `--dangerously-skip-permissions`, Codex `danger-full-access` with `approval_policy = "never"`, and Copilot global auto-approve remove the human entirely.

5. **Test the deny list against the allow list.** A deny list holds only if nothing allowed can do the denied thing another way. `Bash(python3:*)` allowed means `python3 -c` reads `.env` and posts it out while `Read(./.env)` and `Bash(curl:*)` sit in the deny list: those rules bind one tool and one command name, not a process. The only thing that binds every subprocess is the sandbox.

6. **Check the sandbox and what it does not cover.** Strict means `"enabled": true` and `"allowUnsandboxedCommands": false`; with `true`, a command that fails in the sandbox can retry outside it. `excludedCommands` always run outside. `network.allowedDomains` lists only the hosts the work needs: `*.githubusercontent.com` or a paste host lets anyone publish the payload or receive the data. The sandbox covers shell commands only: **hooks, MCP servers and the file and web tools run outside it**, so a strict sandbox fixes none of the findings about them.

7. **Read every command that runs without asking.** Every hook (`SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`, …), `statusLine`, `apiKeyHelper` and similar run shell on an event with no prompt. A hook that downloads and runs code is 🟥: whoever controls that URL runs code on every machine that opens the repo. Replace it with a script committed to the repo, or delete it. Enabled plugins bring hooks and servers these files don't show: list them under "To confirm".

8. **Treat a secret in a committed file as leaked.** A literal token in `env`, `.mcp.json` headers or args, or a connection string with a password, is exposed to everyone with the repo and its history. The fix is **rotate first**, then reference it from the environment (`"${GITHUB_TOKEN}"`) and keep personal files in `.gitignore`. Deleting the line leaves it in git history. Whether the repo was pushed or is public isn't in the files: say so. A plaintext secret in a user-scope file that was never committed (`~/.codex/config.toml`) is moved to the environment, and rotated if a session with no prompts could read it; don't call it committed.

9. **Check each MCP server for pin, publisher, write and mix.** `npx -y pkg` or `pkg@latest` runs whatever the registry serves at start-up; pin an exact version. A publisher the user can't name is unvetted. `enableAllProjectMcpServers: true` starts every server in a cloned repo's `.mcp.json` without approval; `mcp__server` in `allow` approves all its tools, writes included. A server that reads untrusted content (web pages, issues, tickets) in the same session as private data and a way out (shell, write tools, network) is the lethal trifecta: 🟥 when nothing asks.

10. **Check subagents.** A subagent file with no `tools:` line inherits every tool the session has, MCP servers included; give it the list its job needs. `permissionMode: bypassPermissions` on a subagent removes the human for its calls.

11. **Grade, pick the verdict, write the reply.**
    - 🟥 runs or leaks with no person in the way: a hook or setting that runs downloaded code; a literal secret in a committed file; the human removed, or arbitrary code allowed, without a strict sandbox; the trifecta with nothing asking.
    - 🟧 broader than the work, held by one control: the same grants inside a strict sandbox; sandbox escape hatches; wide domains; unpinned or unvetted MCP packages; auto-approved servers; a subagent with no tool list; a bypassable deny list; Codex `inherit = "all"`.
    - 🟨 one change from a hole: a local settings file not git-ignored; `acceptEdits` (edits CI and hook files unprompted).
    - Any 🟥 → **DO NOT USE** until fixed. Any 🟧 → **TIGHTEN BEFORE USE**. Otherwise **SAFE AS CONFIGURED**.

    The reply: the verdict and the worst finding in one or two sentences; then findings worst first, each `file:line`, what it lets happen in one plain sentence, and the replacement config as a snippet; one line on what is fine; "To confirm" last. Snippets in [`reference.md`](reference.md). A chat question about one rule gets a short answer with the replacement, not a full review.

**Non-interactive runs** (subagent, CI, headless): an unknown launch mode or profile is assumed to be the widest one the files define, and an unknown purpose is assumed to be editing and testing the repo, both tagged `[assumption]`. If no configuration file or setting is given at all, emit `BLOCKED: need the agent's configuration files or settings`, then say in plain words which files to send and what the review will contain.

## Useful references in this skill

- [`reference.md`](reference.md) — where each tool keeps its config and how scopes merge, what each wildcard allow entry really permits, the settings that run shell, replacement snippets for Claude Code, Codex, Cursor and VS Code
- [`scripts/agent_config_scan.py`](scripts/agent_config_scan.py) — merges scopes and lists effective grants, hooks, servers, subagents and masked secrets (stdlib only)
- [`examples/python-repo-tighten.md`](examples/python-repo-tighten.md) — worked example: a Python repo with a strict sandbox, a `make` wildcard, an excluded `docker` and an unpinned Slack server; TIGHTEN BEFORE USE

## Quality bar

- **The first line is the verdict** and names the worst finding in plain words.
- **The effective setting is reviewed,** with the winning scope named; scopes not read are listed under "To confirm".
- **Every finding has `file:line`, its effect in one sentence, and replacement config** that can be pasted.
- **Every wildcard allow entry is read as what it can run,** and the deny list is tested against it.
- **Every hook and command-running setting is quoted and judged;** none is waved through as "tooling".
- **Every literal secret says rotate,** masked in the reply, never quoted whole.
- **No invented facts:** no package version, publisher, host, scope or script name the input didn't contain; replacement allow entries use only commands the input shows.
- **No claim about what wasn't read:** plugins, git history, user or managed scopes are "To confirm".

## When to use this skill

- ✅ "Is this repo's Claude Code setup safe to open?" with `.claude/` and `.mcp.json`
- ✅ "Review my `~/.codex/config.toml`" or a Cursor or VS Code agent setup
- ✅ "Is `Bash(npm:*)` OK in our allow list if we deny curl?"
- ✅ Tightening an agent's permissions before rolling the config out to a team

## When NOT to use this skill

- ❌ Choosing which MCP servers and token scopes a workflow should have — `mcp-pairing`
- ❌ Threat-modelling an agent's design for prompt injection and exfiltration paths — `agent-threat-model`
- ❌ Deciding what each subagent should be told and given in a new design — `subagent-design`
- ❌ Writing the organisation's rules for AI tools and data — `ai-usage-policy`
- ❌ A token already leaked or an agent already did damage — `agent-incident-response`; review the config after containment

## Anti-patterns to avoid

- ❌ **Reviewing `settings.json` alone.** The local file, user scope and the profile in use decide what runs.
- ❌ **Trusting the deny list.** `Bash(curl:*)` denied beside `Bash(python3:*)` allowed blocks nothing.
- ❌ **"The sandbox is on, so it's contained."** Not with `allowUnsandboxedCommands: true`, and never for hooks or MCP servers.
- ❌ **Moving the token to an env var and calling it fixed.** It was committed; rotate it.
- ❌ **"Pin it to a safe version"** with a version number the input doesn't show. Say pin to an exact, reviewed version.
- ❌ **A findings table before the verdict,** or a full audit when the question was one rule.
- ❌ **Showing the machinery.** Don't mention this skill, its files or its script in the reply.
- ❌ **A bare `BLOCKED` line.** Keep it, then say in plain words what to send.
