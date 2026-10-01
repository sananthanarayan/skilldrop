---
rfc: 0037
title: Eight new packs and two SRE skills
status: implemented
date: 2026-10-01
author: sananthanarayan
---

# RFC-0037: Eight new packs and two SRE skills

## Problem / use case

The 2026-10-01 comparison with agent-ready-repo found whole jobs skilldrop has no skill for,
where today a user gets a plain-prompt draft instead of a deliverable:
- converting documents between formats
- designing the experience around a product
- running a research question to a sourced answer
- keeping a tracker in step with the plan
- defining the numbers a business runs on
- proving compliance
- writing infrastructure as code
- authoring agent skills themselves

Three of these (data, GRC, skill engineering) neither catalogue covers.

## Fit check

Every skill below meets the four criteria in AGENTS.md:
- **Concrete artifact:** each one names its output file.
- **Portable:** plain folder copy works; scripts are stdlib Python.
- **Opinionated:** each has a quality bar and named anti-patterns.
- **Category:** an existing guide category, or one of the new ones listed below.

Golden rules touched: none. Every new pack `requires` core, has one home per skill
(RFC-0033), and sits at `packs/<pack>/skills/<name>/` (RFC-0034).

## Proposal

| Pack | Skills | Outcome |
|---|---|---|
| `converters` | `md-to-docx`, `md-to-xlsx`, `md-to-html`, `file-to-markdown`, `mermaid-render` (stdlib scripts) | get-a-draft-ready-to-ship |
| `experience-design` | `information-architecture`, `ux-writing`, `content-design`, `design-system-spec`, `service-blueprint` | design-the-experience (new) |
| `research` | `research-plan`, `source-synthesis`, `hypothesis-comparison` | research-a-question (new) |
| `trackers` | `backlog-triage`, `team-status-report`, `tracker-brief-sync` | build-and-review-software; explain-it-to-decision-makers |
| `data-analytics` | `metric-definition`, `sql-review`, `dashboard-spec` | define-and-trust-the-numbers (new) |
| `grc` | `dpia`, `soc2-evidence-map`, `risk-register` | manage-risk-and-compliance (new) |
| `infra-as-code` | `terraform-module`, `terraform-plan-review` | design-the-system; run-and-recover-the-service |
| `skill-engineering` | `skill-author`, `skill-review` | build-agent-skills (new) |
| `sre-oncall` (existing) | `delivery-metrics-report`, `cloud-cost-review` | run-and-recover-the-service |

`slo-definition` was dropped: `observability-plan` already sets SLIs, SLOs, error budgets and
burn-rate alerts. `skill-author` differs from `contribution-wizard`: it writes a portable skill
for any tool and any repo, while `contribution-wizard` adds a skill to this catalogue.
`backlog-triage` differs from `bug-triage`: it works across a whole backlog, not one report.

## Alternatives considered

- **Fold the skills into existing packs.** Rejected: a data analyst or a compliance lead would
  have to install a role pack built for someone else, which defeats the role-based install.
- **Ship them one pack per PR.** Rejected for speed: the packs share no files beyond the
  registries, and one release keeps the changelog and site update coherent.

## Decision

Accepted by the maintainer on 2026-10-01 ("do the new packs and skills point"). Implemented in
the PR that adds this file; ships in 0.14.0.
