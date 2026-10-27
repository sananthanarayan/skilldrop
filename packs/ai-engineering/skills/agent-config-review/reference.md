# agent-config-review — reference

## Where each tool keeps its configuration

| Tool | File | Scope | Holds |
|---|---|---|---|
| Claude Code | managed-settings.json in the system folder (macOS `/Library/Application Support/ClaudeCode/`, Linux and WSL `/etc/claude-code/`), or pushed by an admin | managed | anything below; outranks every other scope |
| Claude Code | `~/.claude/settings.json` | user | every project on the machine |
| Claude Code | `.claude/settings.json` | project | committed, shared with everyone who clones |
| Claude Code | `.claude/settings.local.json` | local | per-person; should be git-ignored |
| Claude Code | `.mcp.json` | project | MCP servers, committed |
| Claude Code | `~/.claude.json` | user and local | MCP servers added with `claude mcp add` (local scope sits under `projects.<path>.mcpServers`) |
| Claude Code | `.claude/agents/*.md`, `~/.claude/agents/*.md` | project, user | subagents: `tools:`, `permissionMode:`, `model:` |
| Claude Code | enabled plugins | any | can add hooks, MCP servers, subagents and commands not visible in the files above |
| Codex | `~/.codex/config.toml`, and a project `.codex/config.toml` if present | user, project | `approval_policy`, `sandbox_mode`, `[sandbox_workspace_write]`, `[shell_environment_policy]`, `[profiles.*]`, `[mcp_servers.*]` |
| Cursor | `.cursor/mcp.json`, `~/.cursor/mcp.json` | project, user | MCP servers |
| Cursor | `.cursor/rules/*.mdc`, `.cursorrules` | project | instructions the agent follows on every request |
| Cursor | `.cursor/cli.json`, `~/.cursor/cli-config.json` | project, user | CLI agent permissions (`Shell(...)`, `Read(...)`, `Write(...)` allow and deny) |
| Cursor | app settings (auto-run, command allowlist) | user | not in the repo; ask for a screenshot or treat as unknown |
| VS Code / Copilot | `.vscode/settings.json`, user settings | project, user | `chat.tools.autoApprove` / `chat.tools.global.autoApprove`, `chat.tools.terminal.autoApprove` |
| VS Code / Copilot | `.vscode/mcp.json` | project | MCP servers under `servers`, secrets via `inputs` |
| Any | `package.json`, `Makefile`, shell scripts, CI workflows, devcontainer | project | launch flags: `--dangerously-skip-permissions`, `--permission-mode bypassPermissions`, Codex `--dangerously-bypass-approvals-and-sandbox` / `--yolo`, `--full-auto` |

## How the scopes combine

**Claude Code.** Precedence for a single value, high to low: managed > command-line flags >
local > project > user. Lists (`permissions.allow`, `ask`, `deny`, `additionalDirectories`,
sandbox domain lists) are combined across scopes, not replaced. Rules are evaluated deny first,
then ask, then allow, so a deny in any scope beats an allow in any scope. Hooks from every scope
run. Managed policy can narrow all of this: `allowManagedPermissionRulesOnly` (only managed
rules count), `allowManagedHooksOnly` (only managed hooks run), and
`permissions.disableBypassPermissionsMode: "disable"` (bypass mode can't be turned on).
Project settings take effect once the user trusts the folder.

**Codex.** Command-line flags (`-c key=value`, `--sandbox`, `--ask-for-approval`) > the profile
named by `--profile` or the top-level `profile` key > top-level keys. A profile that sets
`sandbox_mode` replaces the top-level value for every session launched with it.

**Cursor and VS Code.** User settings apply everywhere; workspace settings override them for the
folder. An MCP server defined in both a project and a user file runs from whichever the tool
loads for that name; list both.

## What a wildcard allow entry really permits

`Bash(x:*)`, `Bash(x *)` and `Bash(x*)` all mean "any command starting with `x`, any arguments".

| Entry | What it lets run without asking |
|---|---|
| `Bash`, `Bash(*)` | any shell command |
| `Bash(python3:*)`, `node`, `ruby`, `perl`, `php`, `deno`, `bun` | any code (`-c`, `-e`) |
| `Bash(bash:*)`, `sh`, `zsh`, `pwsh` | any shell |
| `Bash(npm:*)`, `pnpm`, `yarn` | any `package.json` script; `npm exec` / `dlx` download and run any package |
| `Bash(npx:*)`, `bunx`, `uvx`, `pipx` | download and run any package |
| `Bash(pip:*)`, `uv` | package installs whose setup code runs; `uv run` runs anything |
| `Bash(make:*)`, `just`, `cargo`, `go` | whatever the build file says; `go run`, `cargo run`, build scripts |
| `Bash(docker:*)`, `docker compose`, `podman` | containers that mount the host disk (`-v /:/host`) or run privileged |
| `Bash(kubectl:*)` | anything the kubeconfig's cluster role allows |
| `Bash(git:*)` | `git -c core.sshCommand=…`, aliases and repo hooks run commands; `git push` sends code to any remote |
| `Bash(gh:*)` | `gh api` calls anything the token allows, deletes included |
| `Bash(curl:*)`, `wget` | uploads any file to any host; downloads code |
| `Bash(ssh:*)`, `scp`, `rsync` | commands on other machines; copies data off this one |
| `Bash(find:*)`, `xargs`, `env`, `sudo`, `timeout`, `nohup`, `watch` | whatever command follows (`find -exec`, `xargs sh`) |
| `Bash(awk:*)`, `sed` | commands via `system()` or GNU sed's `e` |
| `Edit`, `Write` with no path | any file, the agent's own settings, hooks and CI files included |
| `WebFetch` with no domain | any URL; the query string carries data out |
| `mcp__server` or `mcp__server__*` | every tool on that server, writes included |

Exact entries are safe to allow: `Bash(npm run test)`, `Bash(npm run lint)`, `Bash(git status)`,
`Bash(git diff:*)`, `Bash(git log:*)`, `WebFetch(domain:docs.example.com)`,
`mcp__github__get_pull_request`. Use only command and script names the input shows.

## Settings that run shell without asking

- `hooks` — every event: `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `SubagentStop`, `PreCompact`, `SessionEnd`. A hook gets the tool input on stdin and runs with the user's full access, outside the sandbox.
- `statusLine` (`type: command`) — runs repeatedly while the session is open.
- `apiKeyHelper`, `awsAuthRefresh`, `awsCredentialExport`, `otelHeadersHelper` — run to fetch credentials.
- MCP servers with a `command` — start when the session does, outside the sandbox.
- Codex `[mcp_servers.*]` and Cursor `.cursor/mcp.json` servers — same.

Downloaded-and-run is the critical shape: a fetch (`curl`, `wget`, `Invoke-WebRequest`, a URL)
piped into an interpreter, or saved and then executed. Whoever can change the remote file runs
code on every machine, every session.

## Sandbox keys (Claude Code)

| Key | Strict value | Wrong value means |
|---|---|---|
| `sandbox.enabled` | `true` | shell commands run with the user's full access |
| `sandbox.allowUnsandboxedCommands` | `false` | a command that fails in the sandbox retries outside it |
| `sandbox.excludedCommands` | `[]` | those commands always run outside |
| `sandbox.network.allowedDomains` | the hosts the work needs | wildcards and open-publish hosts (`*.githubusercontent.com`, gist and paste sites, tunnels) are a payload source and a drop box |
| `sandbox.autoAllowBashIfSandboxed` | either, if strict | when on, sandboxed commands run without a prompt, so the sandbox is the only control |
| `sandbox.failIfUnavailable` | `true` where policy requires it | the session starts unsandboxed when the OS sandbox is missing |

Codex equivalents: `sandbox_mode = "workspace-write"` (not `danger-full-access`),
`[sandbox_workspace_write] network_access = false`, `approval_policy = "on-request"` or
`"untrusted"` (not `"never"` outside a disposable container).

## Replacement snippets

**Claude Code project settings, tightened** — exact commands, deny kept, strict sandbox:

```json
{
  "permissions": {
    "allow": ["Bash(npm run test)", "Bash(npm run lint)", "Bash(git status)", "Bash(git diff:*)"],
    "deny": ["Read(./.env)", "Read(./.env.*)", "Read(./secrets/**)", "WebFetch"]
  },
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "network": { "allowedDomains": ["registry.npmjs.org"] }
  },
  "enableAllProjectMcpServers": false
}
```

**A hook that ran a downloaded script** — commit the script, review it, run the local copy:

```json
"hooks": {
  "SessionStart": [
    { "hooks": [ { "type": "command", "command": "bash ./tools/agent-bootstrap.sh" } ] }
  ]
}
```

**`.mcp.json` with no secret and a pinned package:**

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "<package>@<exact-reviewed-version>"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" }
    }
  }
}
```

**A subagent with only what its job needs:**

```markdown
---
name: db-migrator
description: Writes database migrations. Use when a change needs a schema migration.
tools: Read, Grep, Glob, Edit, Bash
---
```

`Bash` in a subagent's list is still held by the session's permission rules and sandbox, so
the allow list decides which commands it runs without asking. Leave `Bash` out of a subagent
that only reads.

**Codex profile that keeps a person and the sandbox:**

```toml
[profiles.fast]
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[shell_environment_policy]
inherit = "core"
```

**VS Code** — turn off global auto-approve and approve terminal commands exactly:

```json
{
  "chat.tools.autoApprove": false,
  "chat.tools.global.autoApprove": false,
  "chat.tools.terminal.autoApprove": { "npm run test": true, "npm run lint": true }
}
```

**Managed policy lines** an organisation can set so no project can loosen them:

```json
{
  "permissions": { "disableBypassPermissionsMode": "disable" },
  "allowManagedHooksOnly": true
}
```

**Keep personal files out of git:**

```gitignore
.claude/settings.local.json
.env
.env.*
```

If the file is already tracked, an ignore line does nothing until it is untracked:

```bash
git rm --cached .claude/settings.local.json
```

## A secret in a committed file

1. Rotate it at the issuer (revoke the old value, issue a new one with the narrowest scope the work needs).
2. Replace the literal with a reference: `${VAR}` in Claude Code `.mcp.json` and settings `env`, `${env:VAR}` in Cursor, an `inputs` prompt in `.vscode/mcp.json`, the shell environment the server inherits in Codex.
3. Treat the history as exposed: removing the line or rewriting history does not un-leak a value that was pushed or cloned.
4. What can't be told from the files: whether it was pushed, whether the repo is public, what scopes the token has. Each goes under "To confirm".
