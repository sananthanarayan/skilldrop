---
rfc: 0054
title: Permissions for what instructions run, and a scan of agents
status: implemented
date: 2026-10-20
author: sanjay-ananth
---

# RFC-0054: Permissions for what instructions run, and a scan of agents

## Problem / use case

Two gaps the OWASP mapping names as Partial (AST01, AST03):

- **Instructions that run things go undeclared.** A skill with no scripts can still tell the
  agent to run `terraform init`, `curl` a host or `pip install`, and the agent runs it with
  the user's credentials. RFC-0039's `permissions` describes only what scripts do, so these
  skills declared nothing. `--contain` (RFC-0051) then had no hosts to allow, and the reader
  had nothing to check the prose against.
- **Agents aren't scanned.** An agent file is a system prompt the tool adopts whole, with the
  tools its frontmatter grants. `skilldrop scan` read only skills, so an agent that told the
  model to hide its edits, inherited every tool, or skipped approval passed silently. A
  policy's `scan.max` didn't apply to agent installs either.

## Fit check

A change to the manifest contract's meaning (no new field) and to the scan's scope. Golden
rules hold: the CLI stays zero-dependency, nothing is executed, and the scan stays a
heuristic that reports, except where a policy's `scan.max` asks it to refuse.

## Proposal

**Instructions are declared like scripts.** An instruction to run a command belongs in a
fenced `bash`/`sh`/`shell`/`console`/`zsh` block, where a reader sees it. The scan reads each
such block in `SKILL.md`, `reference.md` and `references/*.md`, and from each command takes:

- the program it starts, ignoring `sudo` and environment assignments, and reading
  `python3 -m pip` as `pip`;
- every host in a URL.

Quoted text is an argument, so `grep 'a|b'` is never read as a command named `b`. Shell
builtins and keywords, the text tools every agent already has, and an interpreter running the
skill's own `scripts/` are left out. Every program must appear in `permissions.commands`
(`"*"` covers any), and every host in `permissions.network`. Each gap is a 🟨 finding named
`undeclared-instructed-command` or `undeclared-instructed-network`. Like every `undeclared-*`
finding, it fails `skilldrop validate`. A skill without scripts declares `"files": "none"`.
Declared hosts flow into `--contain`'s allowed domains unchanged.

**Agents get scanned.** `skilldrop scan` with no names covers skills and agents;
`scan --agent [names]` covers agents only, since an agent can share a skill's name. Each agent
gets the prose rules, plus:

| Finding | Severity | When |
|---|---|---|
| `agent-all-tools` | 🟧 | no `tools:` line: the agent inherits every tool, MCP servers included |
| `agent-untrusted-and-act` | 🟧 | it reads from outside (`WebFetch`, `WebSearch`, an `mcp__` tool) and can act (`Bash`, `Write`, `Edit`) in one context |
| `agent-skips-approval` | 🟥 | `permissionMode: bypassPermissions` or `acceptEdits` |
| `agent-hooks` | 🟧 | frontmatter `hooks:` |

A third-party `install --agent` prints the findings, as a skill install does. A policy's
`scan.max` refuses agents above it, before anything is written.

**Bundled catalogue.** The new check flagged five skills, and each one now declares what its
instructions run:

- `sonar-review`: `sonar-scanner`, `git`, `curl` and `sonarcloud.io`.
- `terraform-module`: `terraform` and the Terraform registry hosts.
- `terraform-plan-review`: `terraform`.
- `mermaid-render`: `npm` and `registry.npmjs.org`.
- `figma-diagrams`: `pip` and PyPI.

`dependency-upgrade-review` declares `git`, `gh`, the package managers it inspects, and
`github.com`. The three bundled agents raise no finding.

## Alternatives considered

- **Parse prose for verbs like "run" and "fetch".** Every sentence that mentions running
  something would match, and a skill about security would drown in its own vocabulary. A
  fenced block is the convention the catalogue already follows, and it is checkable.
- **A separate `instructions` block beside `permissions`.** It would double what an author
  maintains, and `--contain` needs one list of hosts. What the agent runs reaches the user's
  machine the same way whether a script or a sentence asked for it.
- **Fail the install on an agent finding.** Many agents need `Bash`. As with skills, the scan
  reports, and an organisation that wants a hard limit sets `scan.max`.

## Decision

Accepted and implemented in 0.16.32.
