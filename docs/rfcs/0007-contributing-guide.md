---
rfc: 0007
title: CONTRIBUTING.md as the human entry point
status: implemented
date: 2026-07-26
author: sananthanarayan
---

# RFC-0007: CONTRIBUTING.md as the human entry point

## Problem / use case

Everything a contributor needs already exists — `AGENTS.md` carries the golden rules, file placement, authoring steps, the pre-commit checklist, and the voice rules; `README.md` **Adding a new skill** carries the eight-step recipe. Neither is discoverable to a human. GitHub surfaces `CONTRIBUTING.md` in the repo sidebar and links it from the new-issue and new-PR pages; it looks for that exact filename and nothing else. A first-time contributor lands on the repo, sees a file named for autonomous agents, and either reads the wrong thing or opens a PR with no RFC, no `evals/`, no pack membership, and a `main`-branch head — every one of which the checklist would have caught.

The second gap is shape. `AGENTS.md` is a reference document ordered by *topic*. A contributor arrives with a *task* — "I want to add a skill", "I want to fix a typo in an existing one", "I want to change the CLI". Those three have materially different gates, and today you have to reconstruct which apply.

## Fit check

Structural change — a new top-level file, which the RFC template lists as requiring an RFC. It touches golden rule 4 (never invent commands or conventions): `CONTRIBUTING.md` must document only the two real checks (`python3 validate.py`, `node bin/skilldrop.js validate`) and the real branch/PR flow, and must not grow a parallel set of rules. It doesn't break it because the file is a **router, not a source of truth** — every rule stays in `AGENTS.md` and is linked, never restated in a way that can drift independently.

## Proposal

`CONTRIBUTING.md` at the repo root, modelled on the shape agent-ready-repo uses (lanes + gates + authority table) but sized to skilldrop's actual machinery — no packs projection, no `make`, no build step:

- **Before you start** — read `AGENTS.md`; the RFC rule (required for a new skill, a new top-level file/directory, a schema change, or a repo-wide convention; not for fixes, doc corrections, or eval additions).
- **The invariant this repo protects** — skills stay flat folders under `skills/`, packs are metadata only, and the name triple-match holds. This is skilldrop's analogue of agent-ready-repo's source-of-truth split, and it is the one thing a well-meaning PR most often breaks.
- **Three contribution lanes** — new skill / change an existing skill / change repo machinery (CLI, `packs.json`, routing, hooks, `validate.py`), each with its own gates.
- **Before you open the PR** — the two commands, the manual test pass, branch naming, commit style.
- **Cutting a release** — bump `package.json`, merge to `main`, CI publishes via npm OIDC and tags `v<version>` (RFC-0004).
- **Where to find authoritative information** — table mapping question → file, so the router role is explicit.
- **When this file is wrong** — flag drift in a PR rather than working around it.

`README.md` and `AGENTS.md` each gain one pointer line. Nothing moves.

## Alternatives considered

- **`.github/CONTRIBUTING.md` instead of the root:** rejected — GitHub honours both, but the root is where a contributor cloning the repo actually looks, and `.github/` here is CI-only.
- **Rename `AGENTS.md` to `CONTRIBUTING.md`:** rejected — breaks the cross-IDE convention that Copilot, Codex, and Cursor read `AGENTS.md`, and the two documents have different readers (agent vs. human) and different ordering (topic vs. task).
- **Restate the rules in `CONTRIBUTING.md` so it stands alone:** rejected — two copies of the pre-commit checklist means one of them is wrong within a release. Link, don't duplicate.
- **Do nothing:** rejected — the guidance exists but is invisible at exactly the moment GitHub would surface it.

## Decision

Implemented as proposed. `CONTRIBUTING.md` shipped at the repo root as a router over `AGENTS.md` — three lanes, the two real gates, the release flow, and the authority table — with pointer lines added to `README.md` and `AGENTS.md`. The same commit records the version-bump rule in **Releasing** (patch digit, one step at a time; minor reserved for a change to the CLI's public surface) and repairs an orphaned sentence fragment stranded in that section.
