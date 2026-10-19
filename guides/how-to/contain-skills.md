---
title: Contain a skill's reach
summary: Run a project's shell commands in Claude Code's sandbox, limited to the folder and the network hosts its skills declare, without loosening anything you already set
kind: how-to
---

# Contain a skill's reach

A skill normally runs with everything your agent can do. With `--contain`, the shell commands
Claude Code runs in a project, and everything they start, can write only inside that project
and reach only the hosts its skills declare. What it writes and the rules it follows are in
[Policy file and audit log](../reference/policy-and-audit.md#containment).

## Install with containment

```bash
skilldrop install figma-diagrams --project --contain
```

It turns on Claude Code's strict sandbox in `.claude/settings.local.json`, your own file, and
keeps that file out of git. It only tightens: anything you already set stays, and it never
widens a sandbox that was already on. A skill that declares writing anywhere on disk is
refused, because it can't run inside the sandbox.

## Check it took

Open the project in Claude Code, accept the prompt to trust the folder (project settings
apply only once you do), and run `/sandbox`.

## Keep the web tools out too

The sandbox covers shell commands only. To keep the agent's web tools out of this project as
well, add to the same file:

```json
"permissions": { "deny": ["WebFetch", "WebSearch"] }
```

## Make it the rule

Add `"require_containment": true` to the organisation policy
([Govern skills across an organisation](govern-skills.md)): installs that aren't contained are
refused, and Claude Code won't start in a contained project if its sandbox can't.

Containment uses Claude Code's sandbox, on macOS, Linux and WSL2. On native Windows, and in
other tools, there is no sandbox to configure; `--contain` prints what the skills expect.
