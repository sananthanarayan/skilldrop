---
rfc: 0051
title: Containment from what a skill declares, set up only by tightening
status: implemented
date: 2026-10-19
author: sanjay-ananth
---

# RFC-0051: Containment from what a skill declares, set up only by tightening

## Problem / use case

An installed skill runs with the agent host's full permissions. A skill whose script calls
one API, or a skill with no scripts at all, gets the same reach as everything else in the
session: every host on the network and every file the user can write. OWASP's Agentic Skills
Top 10 calls this AST06 (Weak Isolation), and it was the one risk the mapping rated **Not
covered**. skilldrop can't sandbox anything itself; it copies files. But Claude Code has a
sandbox, and a skill already says what it needs.

## Fit check

Structural change to the CLI: an `--contain` option and a `require_containment` policy key.
No new manifest field: the `permissions` block a script skill already declares (RFC-0039),
the hosts it contacts and where it writes, is the expectation the sandbox is sized to. A skill
with no scripts needs nothing.

## What the host provides (checked 2026-10-19)

From code.claude.com/docs/en/sandboxing and /permissions:

- Claude Code's sandbox confines shell commands and every process they start: writes to the
  working directory and temp, network only to `sandbox.network.allowedDomains`, which start
  empty. `allowUnsandboxedCommands: false` stops a failed command retrying outside it.
- It covers **shell commands only**. File tools, web tools, MCP servers and hooks follow
  permission rules instead.
- It applies to a whole project session, not to one skill.

## Proposal

`skilldrop install --project --contain` (or `--local --contain`) turns on the strict sandbox
for that project in `.claude/settings.local.json`, the personal file, kept out of git:

- `sandbox.enabled: true` and `sandbox.allowUnsandboxedCommands: false`.
- `sandbox.network.allowedDomains`: exactly the hosts the installed skills declare, and only
  when no settings file the session reads already turns the sandbox on. Adding hosts to a
  sandbox that is on would widen it, so then it names the hosts and leaves the choice to you.
- It refuses a skill that declares writing anywhere (`permissions.files: "anywhere"`): it can't
  run inside the sandbox, and containing everything else around it would be theatre.
- **It only tightens.** It never removes a setting or sets one to something looser; existing
  `excludedCommands` stay, and are named because they run outside the sandbox.
- It says what the sandbox doesn't cover, and gives the deny rules for the web tools.
- A user-scope install is refused with `--contain`: skilldrop won't change your user settings,
  which reach every project. Other tools have no sandbox it can configure; it prints what the
  skills expect.

A policy with `require_containment: true` refuses an install that isn't contained (a project
whose own settings already run the strict sandbox counts), refuses targets that can't be, and
adds `sandbox.failIfUnavailable: true` so Claude Code won't start there without the sandbox.
`skilldrop inventory` reports whether each Claude Code project is contained.

## Alternatives considered

- **A new `permissions.containment` field.** The declaration already exists; a second one
  would drift from it.
- **Write containment on every install.** An installer that changes an agent's security
  settings unasked is itself a risk, and breaks "install copies files". Opt-in, tighten-only,
  and enforceable by policy gives the strict default without that.
- **Deny the web tools by default.** It is a restriction, but it removes WebFetch and
  WebSearch from every session in the project, which a person should choose; the reply gives
  the two-line rule.

## Decision

Implemented in 0.16.28. AST06 moves from Not covered to Partial: shell commands are contained
where Claude Code runs, sized to each skill's declaration; the file and web tools, MCP servers,
other hosts and native Windows are not. Verified against Claude Code 2.1.287: with the
generated settings, a write outside the project failed with "Operation not permitted". A new,
untrusted folder's project settings apply once Claude Code trusts the folder.
