---
title: Policy file and audit log
summary: Every field of the organisation policy, where the CLI looks for it, how it fails, and the format of the audit log and the inventory report
kind: reference
---

# Policy file and audit log

The task-by-task guide is [Govern skills across an organisation](../how-to/govern-skills.md);
the design is [RFC-0050](../../docs/rfcs/0050-org-governance.md). The contract is
[`contracts/policy.schema.json`](../../contracts/policy.schema.json).

## Where the CLI looks

1. `--policy <file>` on the command
2. `SKILLDROP_POLICY`
3. `~/.config/skilldrop/policy.json`

The first one found is the policy. Named (1 or 2) but missing, not valid JSON, or carrying a
key this version doesn't know: the command stops and nothing changes.

## Fields

| Field | Meaning | Absent |
|---|---|---|
| `version` | Always `1` | required |
| `note` | Who owns the policy, where to ask | — |
| `catalogues.allow` | Sources allowed: `"bundled"`, a git URL, or a path. A `*` matches anything, so `https://git.example.org/ai/*` allows every repository under it | any source |
| `catalogues.require_pinned` | `true`: every source but the bundled one must be pinned, `--from <url>#<commit>`. A path on disk can't be pinned, so it is refused | not required |
| `skills.allow` | Names of skills, loops and agents allowed; `*` matches anything | any name |
| `skills.block` | Names refused even when allowed | none |
| `scan.max` | The worst supply-chain scan finding a skill may carry: `none`, `low` (🟨), `medium` (🟧), `high` (🟥). Findings in eval fixtures and example inputs never count | no limit |
| `require_containment` | `true`: an install must be contained ([RFC-0051](../../docs/rfcs/0051-declared-containment.md)): `--contain`, or a Claude Code project whose own settings already run the strict sandbox. Other tools and user-scope installs are refused, and `--contain` also sets `sandbox.failIfUnavailable` | not required |
| `audit.log` | Where the audit log goes | `~/.config/skilldrop/audit.jsonl` |
| `audit.actor` | `"pseudonym"`, `"none"`, `"os-user"`, or `{"fixed": "<name>"}` | `"pseudonym"` |
| `audit.salt_env` | The variable holding the secret salt for pseudonyms | `SKILLDROP_AUDIT_SALT` |

## What each command does with it

| Command | With a policy |
|---|---|
| `install` (skills, `--pack`, `--loop` and its stage skills, `--agent`, `--profile`, `--panel`) | Refuses the whole request, naming each rule broken, before writing anything |
| `update` | Skips each skill or loop the policy now refuses; the installed copy stays as it is |
| `inventory` | Marks each install the policy refuses, and exits 1 if there is one |
| `install`, `update`, `uninstall` with `audit` set | Append one line per skill, loop or agent |

## Containment

`install --project --contain` (or `--local --contain`), [RFC-0051](../../docs/rfcs/0051-declared-containment.md),
changes `.claude/settings.local.json` beside the installed skills, and only by tightening:

| Setting | Set to | When |
|---|---|---|
| `sandbox.enabled` | `true` | always |
| `sandbox.allowUnsandboxedCommands` | `false`: a failed command can't retry outside the sandbox | always |
| `sandbox.network.allowedDomains` | the hosts the skills declare in `permissions.network` | only if no settings file the session reads already turns the sandbox on; otherwise the hosts are named and left to you |
| `sandbox.failIfUnavailable` | `true`: Claude Code won't start without the sandbox | when the policy has `require_containment` |

| Case | What happens |
|---|---|
| A skill declares `permissions.files: "anywhere"` | Refused before anything is copied |
| User-scope install | Refused: user settings reach every project |
| `--ide` other than Claude Code, or `--dest` | Prints what the skills expect; refused under `require_containment` |
| The settings file isn't valid JSON | Refused before anything is copied |
| The file isn't ignored by git | Listed in `.git/info/exclude` |
| Existing `excludedCommands` | Kept, and named: they run outside the sandbox |

The sandbox covers shell commands and the processes they start. Claude Code's file and web
tools, MCP servers and hooks follow permission rules instead.

## The audit log

One JSON object per line:

```json
{"ts":"2026-10-19T17:51:58.716Z","action":"install","kind":"skill","name":"adr-generator","version":"0.1.1",
 "source":"bundled","commit":null,"pinned":false,"target":"~/.claude/skills","actor":"p:9f32de76b1705082",
 "policy":"06e39fe160da496b","prev":"<sha-256 of the line before>"}
```

`policy` is the first 16 characters of the SHA-256 of the policy file in force, so you can
tell which version of the policy applied. `prev` chains the lines: `skilldrop audit verify`
recomputes it for every line and names the first that doesn't follow the one before it.
Paths under the home directory are written as `~`. The log is refused inside a git working
tree, and everything it needs (the salt, a writable place) is checked before the command
changes anything. `SKILLDROP_AUDIT_LOG=<file>` turns the log on without a policy.

| `audit.actor` | Each entry names |
|---|---|
| `"pseudonym"` | `p:` and 16 hex characters: an HMAC-SHA-256 of the user and machine name under the organisation's salt. Stable per person and machine; meaningless without the salt |
| `"none"` | no one |
| `"os-user"` | the operating-system user name |
| `{"fixed": "team-platform"}` | that name, for every entry |

## The inventory report

`skilldrop inventory --json` writes `{inventory: 1, created, label, cli, policy, installs: [...]}`,
one install per skill, loop or agent found in any target: `target`, `scope`, `ide`, `kind`,
`name`, `version`, `source`, `commit`, `pinned`, `edited` (files changed since install) and
`policy` (`"ok"`, a list of reasons it is refused, or `null` with no policy). `--merge` reads
any number of these.
