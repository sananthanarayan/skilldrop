---
title: Skills that ship scripts
summary: Every skill that ships scripts and what each declares it needs — packages, environment variables, hosts, programs and files — and how to invoke a skill from Claude Code or any other IDE.
kind: reference
---

# Skills that ship scripts

Many skills ship helper scripts in a `scripts/` folder, and each one declares what its scripts need in its own `manifest.json`: `deps` for packages, `env` for environment variables, and `permissions` for the hosts, commands and files the scripts touch. You can read that block before you install.

Most scripts run on the Python standard library. Two need a package: `deck-builder` (`python-pptx`) and `figma-diagrams` (`requests`). [Installing dependencies](install-targets.md#installing-dependencies) covers both.

## Every skill with scripts

What each one declares in its manifest: the packages to install, the environment variables it reads, the hosts its scripts contact, the programs they run, and which files they touch (`named-paths` means only paths you pass in). The table is generated from the manifests.

<!-- scripts:start -->
| Skill | Pack | Packages | Environment | Network | Runs | Files |
|---|---|---|---|---|---|---|
| [`agent-config-review`](../../packs/ai-engineering/skills/agent-config-review/SKILL.md) | ai-engineering | — | — | — | `git` | named-paths |
| [`agent-incident-response`](../../packs/ai-engineering/skills/agent-incident-response/SKILL.md) | ai-engineering | — | — | — | `git` | named-paths |
| [`ai-usage-report`](../../packs/ai-engineering/skills/ai-usage-report/SKILL.md) | ai-engineering | — | — | — | — | named-paths |
| [`backlog-triage`](../../packs/trackers/skills/backlog-triage/SKILL.md) | trackers | — | — | — | — | named-paths |
| [`behaviour-equivalence`](../../packs/dev-team/skills/behaviour-equivalence/SKILL.md) | dev-team | — | — | — | — | named-paths |
| [`brand-kit`](../../packs/design/skills/brand-kit/SKILL.md) | design | — | — | — | — | none |
| [`cloud-cost-review`](../../packs/sre-oncall/skills/cloud-cost-review/SKILL.md) | sre-oncall | — | — | — | — | named-paths |
| [`codebase-tour`](../../packs/dev-team/skills/codebase-tour/SKILL.md) | dev-team | — | — | — | — | none |
| [`content-design`](../../packs/experience-design/skills/content-design/SKILL.md) | experience-design | — | — | — | — | none |
| [`cover-letter`](../../packs/career/skills/cover-letter/SKILL.md) | career | — | — | — | — | named-paths |
| [`deck-builder`](../../packs/design/skills/deck-builder/SKILL.md) | design | `python-pptx==1.0.2` | — | — | — | named-paths |
| [`delivery-metrics-report`](../../packs/sre-oncall/skills/delivery-metrics-report/SKILL.md) | sre-oncall | — | — | — | — | named-paths |
| [`dependency-upgrade-review`](../../packs/dev-team/skills/dependency-upgrade-review/SKILL.md) | dev-team | — | — | `github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`, `proxy.golang.org` | `git`, `gh`, `npm`, `pip`, `go` | named-paths |
| [`event-contract-draft`](../../packs/solution-architect/skills/event-contract-draft/SKILL.md) | solution-architect | — | — | — | — | named-paths |
| [`feedback-synthesis`](../../packs/product-manager/skills/feedback-synthesis/SKILL.md) | product-manager | — | — | — | — | named-paths |
| [`figma-diagrams`](../../packs/solution-architect/skills/figma-diagrams/SKILL.md) | solution-architect | `requests==2.34.2` | `FIGMA_TOKEN` | `api.figma.com`, `pypi.org`, `files.pythonhosted.org` | `pip` | named-paths |
| [`file-to-markdown`](../../packs/converters/skills/file-to-markdown/SKILL.md) | converters | — | — | — | `pdftotext`, `pdftoppm`, `tesseract` | named-paths |
| [`hypothesis-comparison`](../../packs/research/skills/hypothesis-comparison/SKILL.md) | research | — | — | — | — | named-paths |
| [`interactive-diagram`](../../packs/solution-architect/skills/interactive-diagram/SKILL.md) | solution-architect | — | — | — | — | project |
| [`lean-canvas`](../../packs/product-manager/skills/lean-canvas/SKILL.md) | product-manager | — | — | — | — | named-paths |
| [`marketing-flyer`](../../packs/design/skills/marketing-flyer/SKILL.md) | design | — | — | — | `google-chrome`, `chromium`, `chrome` | named-paths |
| [`md-to-confluence`](../../packs/converters/skills/md-to-confluence/SKILL.md) | converters | — | `CONFLUENCE_EMAIL (optional)`, `CONFLUENCE_API_TOKEN (optional)`, `CONFLUENCE_PAT (optional)` | `*.atlassian.net` | — | named-paths |
| [`md-to-docx`](../../packs/converters/skills/md-to-docx/SKILL.md) | converters | — | — | — | — | named-paths |
| [`md-to-html`](../../packs/converters/skills/md-to-html/SKILL.md) | converters | — | — | — | — | named-paths |
| [`md-to-pptx`](../../packs/converters/skills/md-to-pptx/SKILL.md) | converters | — | — | — | — | named-paths |
| [`md-to-xlsx`](../../packs/converters/skills/md-to-xlsx/SKILL.md) | converters | — | — | — | — | named-paths |
| [`mermaid-render`](../../packs/converters/skills/mermaid-render/SKILL.md) | converters | — | — | `registry.npmjs.org` | `mmdc`, `npm` | named-paths |
| [`output-hygiene`](../../packs/core/skills/output-hygiene/SKILL.md) | core | — | — | — | — | named-paths |
| [`pre-merge-review`](../../packs/dev-team/skills/pre-merge-review/SKILL.md) | dev-team | — | — | — | `git`, `ruff`, `mypy`, `pytest`, `*` | project |
| [`rendering-strategy`](../../packs/frontend/skills/rendering-strategy/SKILL.md) | frontend | — | — | — | — | named-paths |
| [`resume-tailor`](../../packs/career/skills/resume-tailor/SKILL.md) | career | — | — | — | — | named-paths |
| [`risk-register`](../../packs/grc/skills/risk-register/SKILL.md) | grc | — | — | — | — | named-paths |
| [`rollout-plan`](../../packs/dev-team/skills/rollout-plan/SKILL.md) | dev-team | — | — | — | — | none |
| [`skill-review`](../../packs/skill-engineering/skills/skill-review/SKILL.md) | skill-engineering | — | — | — | — | named-paths |
| [`slo-spec`](../../packs/sre-oncall/skills/slo-spec/SKILL.md) | sre-oncall | — | — | — | — | named-paths |
| [`source-synthesis`](../../packs/research/skills/source-synthesis/SKILL.md) | research | — | — | — | — | named-paths |
| [`sql-review`](../../packs/data-analytics/skills/sql-review/SKILL.md) | data-analytics | — | — | — | — | named-paths |
| [`team-status-report`](../../packs/trackers/skills/team-status-report/SKILL.md) | trackers | — | — | — | — | named-paths |
| [`terraform-plan-review`](../../packs/infra-as-code/skills/terraform-plan-review/SKILL.md) | infra-as-code | — | — | — | `terraform` | named-paths |
| [`tracker-brief-sync`](../../packs/trackers/skills/tracker-brief-sync/SKILL.md) | trackers | — | — | — | — | named-paths |
| [`web-performance-review`](../../packs/frontend/skills/web-performance-review/SKILL.md) | frontend | — | — | `registry.npmjs.org` | `lighthouse`, `npx` | named-paths |
<!-- scripts:end -->

## Invoke a skill

All skills are invoked in chat. Arguments are passed as plain text after the skill's trigger phrase (or via `$ARGUMENTS` when invoked as a slash command in Claude Code).

### `architecture-diagrams`

Natural-language trigger (works in any IDE that has the skill installed):

> Draw me a Mermaid diagram of a three-tier web app on AWS with an ALB, two ECS services, and an RDS Postgres backend.

Slash-command form (Claude Code):

```
/architecture-diagrams three-tier web app on AWS with ALB, two ECS services, RDS Postgres
```

Everything after the slash command becomes `$ARGUMENTS` inside the skill.

### `figma-diagrams`

Natural-language trigger:

> Inspect the structure of this Figma file: https://figma.com/file/abc123/MyArchitecture

Slash-command form (Claude Code):

```
/figma-diagrams inspect https://figma.com/file/abc123/MyArchitecture
/figma-diagrams post-comment https://figma.com/file/abc123/MyArchitecture "Looks good — ship it."
```

The skill parses `$ARGUMENTS` to figure out which Figma URL you mean and which action to take.
