# Guides

Longer-form material that used to live in the README. Split by
[Diátaxis](https://diataxis.fr) **kind** — declared in each page's frontmatter, not implied by
its directory, so the tree stays shallow.

| Kind | Answers |
|---|---|
| **tutorial** | "Let me learn by doing something real." |
| **how-to** | "I have a goal — what are the steps?" |
| **reference** | "What exactly does this field/command do?" |
| **explanation** | "Why is it built this way?" |

## tutorial

- [Follow one change through the loops](tutorial/follow-a-change-through-the-loops.md) — one realistic change walked from a complaint to a closed incident, showing what each gate refuses
- [From complaint to closed incident](tutorial/complaint-to-closed-incident.md) — End-to-end: complaint → discover loop → operate loop → closed incident with updated runbook
- [From idea to shipped feature](tutorial/idea-to-shipped-feature.md) — End-to-end: idea → all four lifecycle loops → shipped feature with postmortem
- [Dev-team workflow](tutorial/dev-team-workflow.md) — story → implementation → review panel → release notes
- [Solution architect workflow](tutorial/solution-architect-workflow.md) — brief → diagrams → ADRs → design doc → threat model → council gate
- [Product manager workflow](tutorial/product-manager-workflow.md) — signal → PR/FAQ → OKRs → PRD → metrics → critique gate
- [AI engineering workflow](tutorial/ai-engineering-workflow.md) — use-case triage → readiness → loop design → threat model → evals → usage report

## how-to

- [Install skills, packs and loops](how-to/install.md) — every route: the CLI for any IDE, the Claude Code plugin marketplace, and by hand
- [Install a skill into your IDE](how-to/install-per-ide.md) — per-IDE steps for every target, plus dependency installs
- [Install a profile](how-to/profiles.md) — named bundles of packs, agents, and loops in one command
- [Author a new skill](how-to/author-a-skill.md) — what a skill must contain and what gates it
- [Author a new loop](how-to/author-a-loop.md) — the closed `loop.json` contract and the gate rules
- [Wire a skill to an event](how-to/wire-a-hook.md) — opt-in hooks, projected per target
- [Publish your own catalogue](how-to/publish-a-catalogue.md) — make `skilldrop --from <you>` work
- [Upgrade installed skills](how-to/upgrade-skills.md) — keep what you have installed current; files you edited are kept and the new version lands beside them as `.upstream`
- [Roll out across your org](how-to/enterprise-distribution.md) — bootstrap the hosted marketplace for every machine in one command
- [Use with Jira](how-to/integrate-with-jira.md) — bug triage, story splitting, implementation loops, and release notes from Jira tickets
- [Use with GitHub Projects](how-to/integrate-with-github-projects.md) — implementation loops, review gates, and release notes linked to GitHub issues
- [Use with Figma](how-to/integrate-with-figma.md) — generate diagrams for FigJam, reverse-engineer decisions from mockups
- [Use with Linear](how-to/integrate-with-linear.md) — triage, story splitting, implementation tracking, and release notes from Linear issues
- [Supply credentials to skills](how-to/supply-credentials.md) — how to set FIGMA_TOKEN, SONAR_TOKEN, and other env vars locally, in CI, and via secret managers

## reference

- [Every skill, by category](reference/skill-catalogue.md) — all the skills, one line each, plus the anatomy every skill folder shares
- [The loops, stage by stage](reference/loops.md) — each loop's stages, gates and generated diagram
- [Skills that ship scripts](reference/skills-with-scripts.md) — the two skills with executable helpers

## explanation

- [Why loops](explanation/loops.md) — why sequencing is its own primitive, and why five loops
- [Cost-aware model routing](../MODEL-ROUTING.md) — abstract tiers and the provider map

Architecture and the enforcement model: [ARCHITECTURE.md](../ARCHITECTURE.md).
Contributor rules and the pre-commit checklist: [AGENTS.md](../AGENTS.md).
