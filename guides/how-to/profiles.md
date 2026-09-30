---
title: Install a profile
summary: Named bundles of packs, agents, and loops — install a complete setup in one command.
kind: how-to
---

# Install a profile

A **profile** is a named install recipe: one command installs a bundle of packs, agents, and loops. It sits above packs in the abstraction hierarchy — a pack says what skills a role needs, a profile says what a fresh machine or a new team member needs to get going.

Profiles are metadata only. Nothing moves into a `profiles/` folder; each skill, agent, and loop stays in its flat location and can belong to any number of profiles.

## Built-in profiles

| Profile | What it installs |
|---|---|
| `starter` | `dev-team` pack + review panel (all 3 reviewer agents) + `build` loop |
| `architect` | `solution-architect` pack + `design` and `ship-a-draft` loops |
| `full` | Every pack, every reviewer agent, every loop |

## List available profiles

```bash
npx skilldrop-cli profiles
```

For machine-readable output:

```bash
npx skilldrop-cli profiles --json
```

## Install a profile

```bash
npx skilldrop-cli install --profile starter
```

This installs each pack, then each loop, then each agent the profile declares. The same flags as a regular install apply — `--project` for project scope, `--ide kiro` for Kiro, `--dest <dir>` for anything else:

```bash
npx skilldrop-cli install --profile starter --project
```

## Install from a third-party catalogue

Profiles in any catalogue you can reach with `--from` work the same way:

```bash
npx skilldrop-cli install --profile starter --from https://github.com/your-org/your-catalogue.git
```

## Author a custom profile

Add an entry to `profiles.json` at the repo root:

```json
{
  "profiles": {
    "my-team": {
      "description": "What our squad installs on day one.",
      "packs": ["dev-team", "stakeholder-comms"],
      "agents": ["devils-advocate", "security-reviewer", "code-quality"],
      "loops": ["build", "ship-a-draft"]
    }
  }
}
```

Every pack, agent, and loop you name must exist — `validate.py` enforces this and fails if any reference is dangling. Run it before committing:

```bash
python3 validate.py
```

Pack names must be keys in `packs.json`. Agent names must match files in `agents/`. Loop names must match folders in `loops/`.
