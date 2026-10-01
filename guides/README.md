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
- [Measure your loops](how-to/measure-your-loops.md) — the opt-in, local-only run log, and which gates pass first time
- [Run a skill in CI](how-to/run-a-skill-in-ci.md) — the GitHub Action: a skill on every pull request, results in the job summary, optional fail on a verdict
- [Roll out across your org](how-to/enterprise-distribution.md) — bootstrap the hosted marketplace for every machine in one command
- [Use with MCP servers](how-to/use-with-mcp-servers.md) — which servers pair with which skills, adding one in each tool, and the security rules
- [Use with Jira](how-to/integrate-with-jira.md) — bug triage, story splitting, implementation loops, and release notes from Jira tickets
- [Use with GitHub Projects](how-to/integrate-with-github-projects.md) — implementation loops, review gates, and release notes linked to GitHub issues
- [Use with Figma](how-to/integrate-with-figma.md) — generate diagrams for FigJam, reverse-engineer decisions from mockups
- [Use with Linear](how-to/integrate-with-linear.md) — triage, story splitting, implementation tracking, and release notes from Linear issues
- [Supply credentials to skills](how-to/supply-credentials.md) — how to set FIGMA_TOKEN, SONAR_TOKEN, and other env vars locally, in CI, and via secret managers

## reference

- [Every skill, by category](reference/skill-catalogue.md) — all the skills, one line each, plus the anatomy every skill folder shares
- [The loops, stage by stage](reference/loops.md) — each loop's stages, gates and generated diagram
- [Skills that ship scripts](reference/skills-with-scripts.md) — the two skills with executable helpers
- [skilldrop and the OWASP Top 10s](reference/owasp-mapping.md) — what skilldrop covers in the Agentic Skills Top 10 and LLM Top 10 2025, and the gaps

## Per pack

A how-to and a reference page for every pack, generated from the pack's own files by
`build_pack_guides.py`.

<!-- pack-guides:start -->
| Pack | How-to | Reference |
|---|---|---|
| Core | [Use the Core pack](how-to/packs/use-the-core-pack.md) | [Core pack reference](reference/packs/pack-core.md) |
| Solution architect | [Use the Solution architect pack](how-to/packs/use-the-solution-architect-pack.md) | [Solution architect pack reference](reference/packs/pack-solution-architect.md) |
| Product manager | [Use the Product manager pack](how-to/packs/use-the-product-manager-pack.md) | [Product manager pack reference](reference/packs/pack-product-manager.md) |
| Dev team | [Use the Dev team pack](how-to/packs/use-the-dev-team-pack.md) | [Dev team pack reference](reference/packs/pack-dev-team.md) |
| SRE / on-call | [Use the SRE / on-call pack](how-to/packs/use-the-sre-oncall-pack.md) | [SRE / on-call pack reference](reference/packs/pack-sre-oncall.md) |
| Stakeholder comms | [Use the Stakeholder comms pack](how-to/packs/use-the-stakeholder-comms-pack.md) | [Stakeholder comms pack reference](reference/packs/pack-stakeholder-comms.md) |
| Design | [Use the Design pack](how-to/packs/use-the-design-pack.md) | [Design pack reference](reference/packs/pack-design.md) |
| AI engineering | [Use the AI engineering pack](how-to/packs/use-the-ai-engineering-pack.md) | [AI engineering pack reference](reference/packs/pack-ai-engineering.md) |
| API builder | [Use the API builder pack](how-to/packs/use-the-api-builder-pack.md) | [API builder pack reference](reference/packs/pack-api-builder.md) |
| Converters | [Use the Converters pack](how-to/packs/use-the-converters-pack.md) | [Converters pack reference](reference/packs/pack-converters.md) |
| Experience design | [Use the Experience design pack](how-to/packs/use-the-experience-design-pack.md) | [Experience design pack reference](reference/packs/pack-experience-design.md) |
| Research | [Use the Research pack](how-to/packs/use-the-research-pack.md) | [Research pack reference](reference/packs/pack-research.md) |
| Trackers | [Use the Trackers pack](how-to/packs/use-the-trackers-pack.md) | [Trackers pack reference](reference/packs/pack-trackers.md) |
| Data and analytics | [Use the Data and analytics pack](how-to/packs/use-the-data-analytics-pack.md) | [Data and analytics pack reference](reference/packs/pack-data-analytics.md) |
| Governance, risk and compliance | [Use the Governance, risk and compliance pack](how-to/packs/use-the-grc-pack.md) | [Governance, risk and compliance pack reference](reference/packs/pack-grc.md) |
| Infrastructure as code | [Use the Infrastructure as code pack](how-to/packs/use-the-infra-as-code-pack.md) | [Infrastructure as code pack reference](reference/packs/pack-infra-as-code.md) |
| Skill engineering | [Use the Skill engineering pack](how-to/packs/use-the-skill-engineering-pack.md) | [Skill engineering pack reference](reference/packs/pack-skill-engineering.md) |
<!-- pack-guides:end -->

## explanation

- [Why loops](explanation/loops.md) — why sequencing is its own primitive, and why five loops
- [Cost-aware model routing](../MODEL-ROUTING.md) — abstract tiers and the provider map

Architecture and the enforcement model: [ARCHITECTURE.md](../ARCHITECTURE.md).
Contributor rules and the pre-commit checklist: [AGENTS.md](../AGENTS.md).
