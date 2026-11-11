---
rfc: 0082
title: Installing across skilldrop and agent-ready-repo, without one catalogue's skill silently replacing the other's
status: implemented
date: 2026-11-11
author: sanjay-ananth
---

# RFC-0082: Installing across skilldrop and agent-ready-repo, without one catalogue's skill silently replacing the other's

## Problem / use case

Someone who installs from both skilldrop and
[agent-ready-repo](https://github.com/eugenelim/agent-ready-repo) gets packs from both into one
skills folder. A test of both directions on 2026-11-11 found:

- **skilldrop-cli reads his catalogue** (RFC-0014's reader): all 133 of his skills.
- **His installer, `agentbundle`, refused 4 of skilldrop's 25 packs** at first, `core` among
  them, and 3 more once those were fixed. Three causes:
  - a hidden file in a skill folder: 41 entries, all eval fixtures or example inputs, such as
    `.github/workflows/ci.yml.fixture` and `.mcp.json`;
  - a `SKILL.md` below a skill's own (5 fixtures of skills that review skills);
  - a `{` in one description, which its frontmatter reader takes for a nested value.
- **Seven skill names are in both catalogues, as different skills:** `content-design`,
  `devils-advocate`, `file-to-markdown`, `information-architecture`, `rendering-strategy`,
  `service-blueprint` and `ux-writing`. Installing his `ux-writing` after skilldrop's replaced it
  without a word, and left skilldrop's `templates/` and `examples/` mixed in with his files.

## Fit check

- **A CLI behaviour change:** the silent replace becomes a refusal, with one new flag. That's a
  minor release under RFC-0064. It also fixes unsafe behaviour, so it is not a break: no
  documented flag or exit code changes meaning.
- **A fixture-naming convention:** an extension of RFC-0058's `<name>.fixture`.
- **Two guides, a weekly workflow and a hash-locked CI tool.** No skill's instructions change,
  except one description reworded.

## Proposal

**The CLI.**
- **Refuse, don't replace.** `install` refuses a skill already installed from a different
  catalogue, names both sources, and offers `--replace` or a separate `--dest`. `--dry-run`
  shows the refusal.
- **`--replace` replaces cleanly.** It removes the old folder first, so nothing of the other
  skill is left.
- **Same catalogue, no refusal.** Two sources count as the same catalogue whatever the ref or
  spelling, so reinstalling from one catalogue is never refused.
- **`doctor`** lists a third-party skill that shares a name with one of skilldrop's own.

**Skill folders every installer can read.** `validate.py` enforces three rules, and
`run_bench.py` restores the real names in a run, so cached runs stay valid:
- **No hidden entry** anywhere in a skill folder: a fixture that needs one is stored as
  `dot.<name>`.
- **No `SKILL.md` below a skill's own:** a nested one is stored as `SKILL.md.fixture`.
- **No `{` or `}` in a description.**

With these, `agentbundle` installs all 25 packs in full.

**Docs.**
- [Use skilldrop with agent-ready-repo](../../guides/how-to/use-with-agent-ready-repo.md)
  installs each catalogue's packs with the other's installer.
- [skilldrop and agent-ready-repo, side by side](../../guides/reference/agent-ready-repo-map.md)
  maps the packs that cover the same work, and the seven shared names. It describes his skills
  from his catalogue and doesn't rate them.

**A weekly check.** `.github/workflows/interop.yml` checks four things:
- skilldrop-cli still reads his catalogue;
- it still installs one of his packs;
- it still refuses the `ux-writing` clash unasked;
- `agentbundle`, installed by hash from `.github/tools/requirements-interop.txt`, still
  installs every skilldrop pack in full.

His format changes often, and a reader that stops parsing it would otherwise fail without
anyone noticing.

## Alternatives considered

- **Rebuild the outbound export** that RFC-0027 retired, as `pack.toml` per pack. `agentbundle`
  now installs a pack's folder directly, so skill folders it can read are enough. An export
  would bring back the re-alignment work RFC-0027 retired.
- **Rename skilldrop's seven skills.** A name is part of RFC-0064's stability promise, and the
  clash goes both ways. The refusal protects users whichever catalogue they installed first,
  and agreeing names is a conversation with the other maintainer.
- **Benchmark the overlapping skills head to head.** That would publish quality numbers about
  someone else's skills. It's not done without his agreement.

## Decision

Implemented in 1.13.0.
