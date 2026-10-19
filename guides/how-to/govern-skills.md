---
title: Govern skills across an organisation
summary: Decide which catalogues and skills people may install, see what is installed on every machine, and keep a log of every change that shows if it was edited
kind: how-to
---

# Govern skills across an organisation

Three things, all done by the `skilldrop` CLI on each machine, with nothing to host: a policy
it enforces, an inventory you collect, and an audit log you can check. The policy's fields are
in [Policy file and audit log](../reference/policy-and-audit.md).

## Write the policy

Start from [`contracts/policy.example.json`](../../contracts/policy.example.json) and keep it
to the rules you mean:

```json
{
  "version": 1,
  "note": "Platform Security owns this policy. Ask in #ai-tools before adding a catalogue.",
  "catalogues": { "allow": ["bundled", "https://git.example.org/ai/skills"], "require_pinned": true },
  "skills": { "allow": ["*"], "block": ["figma-diagrams"] },
  "scan": { "max": "medium" },
  "audit": { "actor": "pseudonym" }
}
```

Check it before you hand it out; a policy with a mistake stops every install:

```bash
skilldrop install adr-generator --dest /tmp/policy-check --policy policy.json --dry-run
```

## Hand it out

Put it where the CLI looks, on every machine, the way you hand out other configuration (MDM,
a dotfiles repository, an image):

```bash
mkdir -p ~/.config/skilldrop && cp policy.json ~/.config/skilldrop/policy.json
# or point at a managed copy:
export SKILLDROP_POLICY=/etc/skilldrop/policy.json
```

From then on, `install` refuses anything the policy forbids before it writes a file, and
names the rule; `update` skips what the policy now refuses and leaves it as it is.

## Turn on the audit log

With `audit` in the policy, every install, update and uninstall appends a line to
`~/.config/skilldrop/audit.jsonl`. Entries name a pseudonym, which needs your organisation's
secret salt on each machine:

```bash
export SKILLDROP_AUDIT_SALT=<the salt your organisation keeps>
skilldrop audit show --last 10
skilldrop audit verify          # exits 1 and names the line if one was edited or removed
```

Keep the salt secret: with it, you can match a pseudonym to a person from your own records;
without it, nobody who sees the log can.

## Collect an inventory

On each machine, write a report and send it wherever you collect such things:

```bash
skilldrop inventory --json --label "$(hostname)" > inventory-$(hostname).json
```

Then combine them:

```bash
skilldrop inventory --merge inventory-*.json
```

Each line is one skill from one catalogue, on how many machines, at which versions, how many
copies are unpinned or edited, and how many the policy refuses. `inventory` exits 1 when the
policy refuses anything installed, so a scheduled job can alert on it.

## Check an internal mirror

If you host a vetted subset made with `skilldrop package`, check it hasn't changed since:

```bash
skilldrop verify-mirror ./skills-mirror
```

It names every file changed, missing or added since `MIRROR.json` was written, and exits 1 if
there is one.

## What this does not cover

The policy governs installs made with the CLI. A folder copied by hand, or a plugin installed
through Claude Code's marketplace, never passes through it; `skilldrop inventory` still lists
what the CLI installed, and nothing else.
