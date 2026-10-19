---
rfc: 0050
title: An organisation policy the installer enforces, with an inventory and an audit log
status: implemented
date: 2026-10-19
author: sanjay-ananth
---

# RFC-0050: An organisation policy the installer enforces, with an inventory and an audit log

## Problem / use case

A team that adopts skilldrop across forty laptops can't say which skills are installed where,
can't stop someone installing from an unvetted catalogue, and can't show afterwards who
changed what. Everything the CLI knows is per machine: each target's ledger, `doctor`,
`outdated`. OWASP's Agentic Skills Top 10 names this AST09 (No Governance), and the mapping
rated it Partial: "no organisation-wide inventory, approval flow or audit log".

## Fit check

Structural change to the CLI: a new module (`bin/governance.js`), three commands
(`inventory`, `audit`, `verify-mirror`), a `--policy` option, and a closed contract
(`contracts/policy.schema.json`). No skill, pack or loop changes. Zero runtime dependencies,
as before.

## Proposal

- **A policy file the installer enforces**, from `--policy`, then `SKILLDROP_POLICY`, then
  `~/.config/skilldrop/policy.json`. It can allow only some catalogues and require them pinned
  to a commit, allow or block skills, loops and agents by name, and cap the worst
  supply-chain scan finding a skill may carry. `install` (skills, loops and their stage
  skills, agents, profiles, panels) refuses the whole request before writing anything;
  `update` skips what the policy now refuses; `inventory` reports it. The policy **fails
  closed**: named but missing, unreadable, or carrying a key this version doesn't know, it
  stops the command, because a misspelt rule that is silently ignored is a rule that isn't
  there.
- **An inventory**: `skilldrop inventory` reads every target's ledger on a machine (each
  `--ide`, user and project scope, and the agent folders) into one report, `--json` for
  collection, and `--merge` combines many reports into one view: which skills, from where, on
  how many machines, at which versions, how many unpinned or edited, how many the policy
  refuses. Paths under the home directory are written as `~`, so a report names no one.
- **An audit log**, turned on by the policy (or `SKILLDROP_AUDIT_LOG`): one JSON line per
  install, update and uninstall, each carrying the SHA-256 of the line before it, so an
  edited, removed or inserted line breaks the chain and `skilldrop audit verify` says where.
  By default an entry names a **pseudonym** (a keyed hash of user and machine, needing a salt
  the organisation keeps); `"none"`, `"os-user"` and a fixed actor are the alternatives. The
  log is refused inside a git working tree. Everything it needs is checked before a command
  changes anything, so an install can't land and then fail to be recorded.
- **`skilldrop verify-mirror <dir>`** checks an internal mirror against the SHA-256s its
  `MIRROR.json` recorded, and names files changed, missing or added since it was packaged.

## Alternatives considered

- **A hosted service** for inventory and approval. It would see every machine live, but it
  is a runtime dependency and a data store skilldrop would have to run and secure; reports an
  organisation already collects (MDM, CI) do the same job with nothing new to trust.
- **Real names in the audit log by default.** An audit trail must say who; but a pseudonym the
  organisation can resolve from its own records says who to them and to nobody else who sees
  the file. The organisation can choose real names in its own policy (RFC-0049's reasoning).
- **Warn instead of refuse.** A warning in a CI log is not a control.

## Decision

Implemented in 0.16.27. AST09 moves from Partial to Covered for installs made through the
CLI. Installs that bypass it (a folder copied by hand, the Claude Code plugin marketplace)
are outside what an installer can govern, and the mapping says so.
