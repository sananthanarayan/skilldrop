---
title: Use skills with MCP servers
summary: Pair skilldrop skills and loops with MCP servers so the agent fetches tickets, designs, PRs, incidents, query results and cost data itself, add a server in each supported tool, and do it without handing an attacker your data.
kind: how-to
---

# Use skills with MCP servers

Every skilldrop skill works from text: you paste a ticket, a diff or an incident timeline, and
the skill works on it. An MCP server gives the agent a tool that fetches that text itself, so
"Fetch PROJ-123 and run bug-triage" replaces copy and paste. The skill doesn't change; only
where its input comes from does.

No skill requires an MCP server. Skills stay portable: a skill copied into Aider with no
servers at all still works, and a loop stage that has no server simply takes pasted text.

The tracker guides already cover the per-tool basics for their tracker:
[Jira](integrate-with-jira.md), [Linear](integrate-with-linear.md),
[Figma](integrate-with-figma.md) and [GitHub Projects](integrate-with-github-projects.md).
This guide covers which servers pair with which skills, how to add one in each tool, and the
security rules.

## Which server pairs with which skill

Prefer the official server, the one the vendor maintains. Every server below is official
unless the row says otherwise. Check the vendor's docs for the exact setup; the endpoints
below were current on 2026-10-01.

| MCP server | What it fetches | Skills and loops | Starter prompt |
|---|---|---|---|
| **GitHub** (official, `https://api.githubcopilot.com/mcp/`) | Pull requests, diffs, issues, releases, Actions runs | `pre-merge-review`, `release-notes`, `backlog-triage`, `tracker-brief-sync`, the `build` loop | *"Fetch PR #482 in acme/web with its diff and run pre-merge-review."* |
| **Atlassian** (official, Jira and Confluence, `https://mcp.atlassian.com/v2/mcp`) | Jira issues, epics and sprints; Confluence pages | `bug-triage`, `backlog-triage`, `team-status-report`, `user-story-splitter`, `prd-draft` | *"Fetch every open bug in project PAY created this week and run backlog-triage."* |
| **Linear** (official, `https://mcp.linear.app/mcp`) | Issues, projects, cycles | `bug-triage`, `backlog-triage`, `team-status-report`, `user-story-splitter`, `prd-draft` | *"Fetch the current cycle for team ENG and run team-status-report."* |
| **Figma** (official, `https://mcp.figma.com/mcp`) | Frames, components, variables, layout | `figma-diagrams`, `design-system-spec`, `information-architecture` | *"Fetch the components and variables in this Figma file and run design-system-spec."* |
| **Sentry** (official, `https://mcp.sentry.dev/mcp`) | Issues, events, stack traces, releases | `incident-comms`, `postmortem-generator`, the `operate` loop | *"Fetch Sentry issue WEB-3F1 with its latest event and run incident-comms for an internal update."* |
| **Supabase** (official, Postgres, `https://mcp.supabase.com/mcp`) | Schemas, tables, query results | `sql-review`, `metric-definition`, `dashboard-spec` | *"List the tables in the analytics schema, then run metric-definition for weekly active accounts."* |
| **AWS Billing and Cost Management** (official, AWS Labs, local: `awslabs.billing-cost-management-mcp-server`) | Cost Explorer spend, budgets, anomalies, Savings Plans and RI coverage | `cloud-cost-review` | *"Fetch last month's cost by service and any cost anomalies, then run cloud-cost-review."* |
| **Slack** (official, `https://mcp.slack.com/mcp`) | Channel history, threads, search | `incident-comms`, `exec-summary`, `decision-log` | *"Read the #inc-2041 channel since 09:00 and run decision-log on the decisions made."* |

Notes on the rows:

- **Postgres.** The old reference server, `@modelcontextprotocol/server-postgres`, was archived
  on 29 May 2025 and gets no security fixes. Don't use it. Use the server your database
  vendor maintains. The row shows Supabase because its docs cover read-only mode and project
  scoping. For another host, check that vendor's docs.
- **Cloud cost.** The AWS server is the one verified here. For Azure or Google Cloud billing,
  check the vendor's docs for an official server before you install anything.
- **Slack** only lets directory-published or internal Slack apps use MCP, and workspace
  admins approve the client. Slack lists Claude Code and Cursor as supported clients. Check
  Slack's docs for setup in your tool.
- **Figma** only accepts clients listed in its MCP catalogue. There is also a desktop server at
  `http://127.0.0.1:3845/mcp` for people who run the Figma desktop app.
- **Sentry** uses OAuth on the remote server. A local alternative,
  `npx @sentry/mcp-server`, reads a `SENTRY_ACCESS_TOKEN`.

### Running a loop with servers

A loop doesn't know about servers. You fetch each stage's input and hand it over. In the
`build` loop, for example:

```
Fetch issue #311 from acme/web and run the build loop on it. Use the issue text as the input to
the shape stage. At the verify stage, fetch the PR diff before running pre-merge-review.
```

In the `operate` loop, the `respond` and `learn` stages (`incident-comms`,
`postmortem-generator`) get the most from Sentry and Slack: the incident timeline is already
there.

## Add a server in each tool

Each example below adds one remote server and, where useful, one local (stdio) server. Tokens
come from environment variables, never from the file. See
[Supply credentials to skills](supply-credentials.md) for setting them.

### Claude Code

Add a remote HTTP server, then authenticate:

```bash
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
```

Run `/mcp` inside Claude Code and follow the browser login, or run
`claude mcp login sentry`.

Add a local stdio server. Everything after `--` is the command that starts the server:

```bash
claude mcp add --transport stdio \
  --env AWS_PROFILE=cost-readonly --env AWS_REGION=us-east-1 \
  aws-billing -- uvx awslabs.billing-cost-management-mcp-server@latest
```

Pick where the server is stored with `--scope`:

| Scope | Loads in | Shared | Stored in |
|---|---|---|---|
| `local` (default) | This project only | No | `~/.claude.json` |
| `project` | This project only | Yes, through version control | `.mcp.json` at the project root |
| `user` | All your projects | No | `~/.claude.json` |

`.mcp.json` is committed, so it must hold variable names, not values. Claude Code expands
`${VAR}` and `${VAR:-default}`:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/readonly",
      "headers": { "Authorization": "Bearer ${GITHUB_PAT}" }
    }
  }
}
```

`claude mcp list`, `claude mcp get <name>` and `claude mcp remove <name>` manage what you've
added.

### Cursor

Put servers in `.cursor/mcp.json` for one project or `~/.cursor/mcp.json` for all of them.
Cursor reads environment variables with `${env:NAME}`:

```json
{
  "mcpServers": {
    "github": {
      "url": "https://api.githubcopilot.com/mcp/readonly",
      "headers": { "Authorization": "Bearer ${env:GITHUB_PAT}" }
    },
    "aws-billing": {
      "command": "uvx",
      "args": ["awslabs.billing-cost-management-mcp-server@latest"],
      "env": { "AWS_PROFILE": "cost-readonly", "AWS_REGION": "us-east-1" }
    }
  }
}
```

### Codex

Codex reads `~/.codex/config.toml`, or `.codex/config.toml` in a trusted project. The CLI, the
IDE extension and the desktop app share it. Each server is a `[mcp_servers.<name>]` table:

```toml
[mcp_servers.github]
url = "https://api.githubcopilot.com/mcp/readonly"
bearer_token_env_var = "GITHUB_PAT"

[mcp_servers.aws-billing]
command = "uvx"
args = ["awslabs.billing-cost-management-mcp-server@latest"]
env_vars = ["AWS_PROFILE", "AWS_REGION"]
```

`bearer_token_env_var` names the variable that holds the token; `env_vars` forwards variables
from your shell. To add a stdio server from the command line, run
`codex mcp add <name> --env VAR=VALUE -- <command>`. For a server that uses OAuth, run
`codex mcp login <name>`.

### VS Code and GitHub Copilot

Put servers in `.vscode/mcp.json`. The top-level key is `servers`, not `mcpServers`. Use
`inputs` so VS Code prompts for the secret instead of storing it in the file:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "github-pat",
      "description": "GitHub read-only token",
      "password": true
    }
  ],
  "servers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/readonly",
      "headers": { "Authorization": "Bearer ${input:github-pat}" }
    },
    "aws-billing": {
      "type": "stdio",
      "command": "uvx",
      "args": ["awslabs.billing-cost-management-mcp-server@latest"],
      "env": { "AWS_PROFILE": "cost-readonly", "AWS_REGION": "us-east-1" }
    }
  }
}
```

Run **MCP: List Servers** from the Command Palette to start, stop or inspect a server.

### Kiro

Put servers in `.kiro/settings/mcp.json` for the workspace or `~/.kiro/settings/mcp.json` for
your user. The workspace file wins when both define the same server. Kiro expands
`${VARIABLE_NAME}`, and asks you to approve each variable before it expands it:

```json
{
  "mcpServers": {
    "github": {
      "url": "https://api.githubcopilot.com/mcp/readonly",
      "headers": { "Authorization": "Bearer ${GITHUB_PAT}" }
    },
    "aws-billing": {
      "command": "uvx",
      "args": ["awslabs.billing-cost-management-mcp-server@latest"],
      "env": { "AWS_PROFILE": "cost-readonly", "AWS_REGION": "us-east-1" },
      "disabledTools": []
    }
  }
}
```

Leave `autoApprove` empty. It lets the listed tools run without asking you.

### Antigravity

Antigravity reads `mcp_config.json` from `~/.gemini/config/mcp_config.json` (global) or
`.agents/mcp_config.json` (workspace). In the IDE, open it from the agent panel: **…** →
**MCP Servers** → **Manage MCP Servers** → **View raw config**. Remote servers use
`serverUrl`, not `url`:

```json
{
  "mcpServers": {
    "sentry": {
      "serverUrl": "https://mcp.sentry.dev/mcp"
    },
    "aws-billing": {
      "command": "uvx",
      "args": ["awslabs.billing-cost-management-mcp-server@latest"],
      "env": { "AWS_PROFILE": "cost-readonly", "AWS_REGION": "us-east-1" }
    }
  }
}
```

Antigravity's docs don't describe environment variable expansion in this file. Keep tokens out
of the workspace file, and check Antigravity's docs before you put a header with a token in
any file.

## Security

An MCP server is a capability you hand the agent, with your credentials. Treat adding one like
granting access to a new colleague you can't fully trust to tell your instructions from a
stranger's.

1. **Read-only tokens, least privilege.** Start every server read-only. Skills only need to
   read: `pre-merge-review` reads a diff, it doesn't merge it.
   - GitHub: use the `/readonly` URL (`https://api.githubcopilot.com/mcp/readonly`) or the
     `X-MCP-Readonly: true` header, and limit toolsets with `X-MCP-Toolsets` (for example
     `repos,issues`). On the local server, use `--read-only` and `GITHUB_TOOLSETS`. Give the
     token only the repositories and scopes it needs.
   - Linear: use `https://mcp.linear.app/mcp/readonly`, request only the `read` OAuth scope,
     or create an API key with only the `Read` permission.
   - Supabase: add the `read_only=true` and `project_ref=<id>` query parameters to the URL,
     and don't point it at production unless you must.
   - AWS: give the profile only the read permissions the server lists for Cost Explorer,
     Budgets and the rest.
   - Atlassian: the server acts with *your* Jira and Confluence permissions. If you can
     delete it, so can the agent.

2. **Watch for the lethal trifecta.** An agent that holds private data, reads untrusted
   content, and has a way to send data out can be talked into leaking that data by text it
   reads. This is a design property, not a bug. One MCP server often adds two legs at once: the
   GitHub server reads your private repos *and* public issue text anyone can write. A Slack
   server reads private channels *and* messages from anyone in them, and can post. Break one
   leg per path: read-only tokens, separate sessions for public and private work, no write or
   network tool in a session that reads untrusted text.

3. **Run `agent-threat-model` on your setup.** Paste your MCP config (with the tokens removed)
   and the skills you plan to run, and ask for the trifecta matrix:

   ```
   Here is my .mcp.json and the skills I run with it: pre-merge-review, backlog-triage,
   incident-comms. Run agent-threat-model.
   ```

   It lists every path that has all three legs and names the fix for each. See
   [agent-threat-model](../../packs/ai-engineering/skills/agent-threat-model/SKILL.md) and,
   for how this maps to `LLM01:2025` prompt injection and `LLM06:2025` excessive agency,
   [skilldrop and the OWASP Top 10s](../reference/owasp-mapping.md). Run it again whenever
   you add a server or widen a token.

4. **Never put a token in a file you commit.** `.mcp.json`, `.cursor/mcp.json`,
   `.vscode/mcp.json` and `.kiro/settings/mcp.json` belong in version control, so they hold
   variable references (`${GITHUB_PAT}`, `${env:GITHUB_PAT}`, `${input:github-pat}`), never
   values. `claude mcp add --env KEY=value` writes the value into `~/.claude.json`, which is
   not in your repo; keep it that way.

5. **A remote server sees what you send it.** Every tool call to a remote server goes to the
   vendor, along with the arguments the agent chose. Before connecting one at work, check your
   organization's data rules. `ai-usage-policy` can write those rules if you don't have them.

6. **Pin local servers.** `uvx package@latest` and `npx package` run whatever was published
   most recently, with your credentials. Replace `@latest` with a version you've reviewed, and
   pin Docker images to a tag or digest. Upgrade on purpose.

7. **Prefer the official server.** A community server is code from a stranger that holds
   your token. If no official server exists, read the source and pin a commit before you run it.

## Troubleshooting

**The server shows as connected, but the skill doesn't use it.** The skill only sees text;
the agent decides whether to call a tool first. Ask it to fetch, then run the skill, in that
order:

- ❌ *"Run bug-triage on PROJ-123."* The agent may ask you to paste the ticket.
- ✅ *"Fetch PROJ-123 from Jira with the Atlassian server, then run bug-triage on it."*

If it still doesn't call the tool, name the tool. In VS Code, reference it in chat with `#`.

**Auth errors.** For OAuth servers, authenticate again: `/mcp` or `claude mcp login <name>` in
Claude Code, `codex mcp login <name>` in Codex. For token servers, check that the variable is
set in the shell that started your editor, not only in a new terminal. Then check the token's
scopes: Sentry's local server, for example, needs a user token with the scopes its README
lists. A 403 on one action with other actions working usually means the token's scope, not the
server, is the problem.

**Too many tools loaded.** Each server adds tools, and a long tool list costs context and
leads the agent to pick the wrong one. Turn off what you don't use:

- Claude Code turns on tool search by default on current models, which handles a long tool
  list for you. Don't turn it off (`ENABLE_TOOL_SEARCH=false`) with many servers connected.
- Codex: `enabled_tools` and `disabled_tools` per server.
- Kiro and Antigravity: `disabledTools` per server.
- Cursor: switch servers on and off under **Customize** in the sidebar.
- At the server: GitHub toolsets, Supabase's `?features=` parameter.

**A big result gets cut off.** Claude Code caps MCP output at 25,000 tokens. Raise it with
`MAX_MCP_OUTPUT_TOKENS=50000 claude`, or ask the agent for a narrower query: one PR, not the
whole repo.

## Sources

Checked 2026-10-01.

- Claude Code MCP: https://code.claude.com/docs/en/mcp
- Cursor MCP: https://cursor.com/docs/context/mcp
- Codex MCP: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- VS Code MCP servers: https://code.visualstudio.com/docs/copilot/customization/mcp-servers
- VS Code MCP configuration reference: https://code.visualstudio.com/docs/agents/reference/mcp-configuration
- Kiro MCP configuration: https://kiro.dev/docs/mcp/configuration/
- Antigravity MCP: https://antigravity.google/docs/mcp
- GitHub MCP server: https://github.com/github/github-mcp-server
- GitHub remote server options: https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md
- GitHub MCP server in Claude Code: https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-claude.md
- Atlassian MCP server: https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/
- Linear MCP server: https://linear.app/docs/mcp
- Figma MCP server: https://developers.figma.com/docs/figma-mcp-server/
- Figma remote server installation: https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/
- Sentry MCP server: https://mcp.sentry.dev/
- Sentry MCP source: https://github.com/getsentry/sentry-mcp
- Supabase MCP server: https://supabase.com/docs/guides/getting-started/mcp
- Archived Postgres reference server: https://github.com/modelcontextprotocol/servers-archived/tree/main/src/postgres
- AWS Billing and Cost Management MCP server: https://awslabs.github.io/mcp/servers/billing-cost-management-mcp-server
- Slack MCP server: https://docs.slack.dev/ai/mcp-server/
