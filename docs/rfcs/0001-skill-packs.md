---
rfc: 0001
title: Skill packs (virtual, role-based)
status: implemented
date: 2026-07-24
author: sananthanarayan
---

# RFC-0001: Skill packs (virtual, role-based)

## Problem / use case

The catalog is 45 skills and growing. A newcomer who is "a PM" or "on-call SRE" has to read the whole README table and run 10+ `cp -R` commands to assemble a working set — and the skills are designed as pipelines (`brief-intake` → `prd-draft` → `user-story-splitter`), so à-la-carte installs routinely miss the companions that make them compose. agent-ready-repo solves this with packs; skilldrop needs the bundle UX without inheriting the structure.

## Fit check

Structural change — touches golden rules 1 and 2 (skills are discovered by path; `skills/` doesn't move). It doesn't break them because packs are **metadata only**: no skill folder moves, every existing install command keeps working, and the plugin-marketplace path is untouched.

## Proposal

- **`packs.json`** (repo root): named, role-based bundles (`solution-architect`, `product-manager`, `dev-team`, `sre-oncall`, `stakeholder-comms`, `ai-engineering`), each a description + flat skill list. Packs may overlap (`brief-intake` serves three roles); every skill must belong to at least one pack.
- **`pack.py`** (repo root, stdlib-only): list packs, list a pack's skills, `--install` into user scope, `--project` scope, or `--dest <dir>` for non-Claude IDEs.
- **`validate.py`** enforces: every pack entry is a real skill folder, and every skill appears in ≥1 pack (a new skill must declare its audience).

## Alternatives considered

- **Physical `packs/<pack>/<skill>` layout (agent-ready-repo's shape):** rejected — breaks path-based discovery, every documented install command, and the copy-install portability premise; forces either duplication or symlinks for skills serving multiple roles.
- **README-only grouping (status quo):** rejected — categories describe what a skill *is*, not who needs it; and prose can't drive a one-command install or be validated.
- **Wait for the npm CLI (`skilldrop install --pack`):** deferred, not rejected — `packs.json` is exactly the data file that CLI will read; `pack.py` is the interim installer.

## Decision

Implemented as proposed. Packs shipped in `packs.json` + `pack.py`, enforced by `validate.py`, documented in README (**Skill packs**) and the CLI design doc (`--pack` flag).
