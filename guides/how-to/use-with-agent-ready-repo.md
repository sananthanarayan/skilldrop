---
title: Use skilldrop with agent-ready-repo
summary: Install agent-ready-repo's packs with skilldrop-cli and skilldrop's packs with agentbundle, and keep the skills both catalogues name the same way from replacing each other.
kind: how-to
---

# Use skilldrop with agent-ready-repo

You can install packs from [agent-ready-repo](https://github.com/eugenelim/agent-ready-repo) with skilldrop-cli, and skilldrop's packs with its installer, `agentbundle`, into the same project.

The two catalogues are separate projects with their own packs. A few skills share a name in both but are different skills, so you keep one of each. [skilldrop and agent-ready-repo, side by side](../reference/agent-ready-repo-map.md) lists those names and which packs cover the same work.

## Install an agent-ready-repo pack with skilldrop-cli

Point `--from` at his repository and name a pack:

```bash
npx skilldrop-cli install --pack desk-research --from https://github.com/eugenelim/agent-ready-repo
```

skilldrop-cli reads his catalogue as it is, copies the pack's skills into `~/.claude/skills`, and records where each came from, so `update` follows his repository. It warns that the catalogue is third-party: read each `SKILL.md` before first use.

## Install a skilldrop pack with agentbundle

`agentbundle` installs from a local folder, so clone skilldrop first:

```bash
git clone https://github.com/sananthanarayan/skilldrop
```

Then install a pack's skills from its folder:

```bash
agentbundle install ./skilldrop/packs/dev-team --all-skills --scope repo --adapter claude-code
```

Every skilldrop pack installs this way. Use `--skill <name>` instead of `--all-skills` for one skill.

## Keep one skill of each name

When a skill of the same name is already installed from the other catalogue, skilldrop-cli stops and says where each came from:

```bash
npx skilldrop-cli install ux-writing
```

To swap to the one you just asked for, rerun with `--replace`, which removes the old folder first. To keep both, install one into another folder with `--dest <dir>`. `npx skilldrop-cli doctor` lists every installed skill that shares a name with one of skilldrop's own.
