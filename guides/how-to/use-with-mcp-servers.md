---
title: Use skills with MCP servers
summary: Pair skilldrop skills and loops with MCP servers so the agent fetches tickets, designs, PRs, incidents, query results and cost data itself, add a server in each supported tool, and do it without handing an attacker your data.
kind: how-to
---

# Use skills with MCP servers

You can connect an MCP server so the agent fetches a ticket, diff or incident itself and hands it to a skill, instead of you pasting it in.

An MCP server is a tool the agent calls to read from a service such as GitHub, Jira or Sentry. No skill needs one: without a server, paste the text and the skill works the same. Which server pairs with which skill, the config for Cursor, Codex, VS Code, Kiro and Antigravity, and the security rules are in [MCP servers and skills](../reference/mcp-servers.md).

## Install the skills

This guide runs `incident-comms` from the `sre-oncall` pack and `agent-threat-model` from the `ai-engineering` pack:

```bash
npx skilldrop-cli install incident-comms agent-threat-model
```

Both skills land in `~/.claude/skills`, ready for any Claude Code session.

## Add the server

Add Sentry's official remote server to Claude Code:

```bash
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
```

Claude Code stores it for this project only; pass `--scope project` to share it through `.mcp.json`.

## Sign in to the server

Sentry uses OAuth, so log in once:

```bash
claude mcp login sentry
```

A browser login opens, and the server's tools become available to the agent.

## Fetch, then run the skill

Ask for the fetch first and the skill second:

```
Fetch Sentry issue WEB-3F1 with its latest event and run incident-comms for an internal update.
```

The agent calls the Sentry tool, then `incident-comms` drafts the update from the event it fetched.

## Check the setup for leaks

An agent that holds private data, reads text anyone can write and can send data out can be tricked into leaking that data. Paste your config with the tokens removed and ask:

```
Here is my .mcp.json and the skills I run with it: incident-comms. Run agent-threat-model.
```

`agent-threat-model` lists every path that combines all three and names the fix for each.

Before you add a server at work, read the [security rules](../reference/mcp-servers.md#security-rules): read-only tokens, no tokens in committed files, and pinned local servers.
