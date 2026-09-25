# Guides

Longer-form material that used to live in the README. Split by
[Diátaxis](https://diataxis.fr) **kind** — declared in each page's frontmatter, not implied by
its directory, so the tree stays shallow.

| Kind | Answers |
|---|---|
| **how-to** | "I have a goal — what are the steps?" |
| **reference** | "What exactly does this field/command do?" |
| **explanation** | "Why is it built this way?" |

## tutorial

- [Follow one change through the loops](tutorial/follow-a-change-through-the-loops.md) — one realistic change walked from a complaint to a closed incident, showing what each gate refuses

## how-to

- [Install a skill into your IDE](how-to/install-per-ide.md) — per-IDE steps for every target, plus dependency installs
- [Author a new skill](how-to/author-a-skill.md) — what a skill must contain and what gates it
- [Author a new loop](how-to/author-a-loop.md) — the closed `loop.json` contract and the gate rules
- [Wire a skill to an event](how-to/wire-a-hook.md) — opt-in hooks, projected per target
- [Publish your own catalogue](how-to/publish-a-catalogue.md) — make `skilldrop --from <you>` work

## reference

- [Skills that ship scripts](reference/skills-with-scripts.md) — the two skills with executable helpers

## explanation

- [Why loops](explanation/loops.md) — why sequencing is its own primitive, and why four loops
- [Cost-aware model routing](../MODEL-ROUTING.md) — abstract tiers and the provider map

Architecture and the enforcement model: [ARCHITECTURE.md](../ARCHITECTURE.md).
Contributor rules and the pre-commit checklist: [AGENTS.md](../AGENTS.md).
