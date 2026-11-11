---
title: skilldrop and agent-ready-repo, side by side
summary: Which skilldrop packs and agent-ready-repo packs cover the same work, the skill names both catalogues use for different skills, and what each catalogue has that the other doesn't.
kind: reference
---

# skilldrop and agent-ready-repo, side by side

This page maps skilldrop's packs to [agent-ready-repo](https://github.com/eugenelim/agent-ready-repo)'s, for anyone installing from both. How to install each with the other's installer is in [Use skilldrop with agent-ready-repo](../how-to/use-with-agent-ready-repo.md).

Descriptions of agent-ready-repo's skills are taken from its own catalogue. This page doesn't rate them: skilldrop's benchmark measures skilldrop's skills only.

## The same name, a different skill

Both catalogues ship a skill with each of these names. They are separate skills, and a skills folder holds one of each name. skilldrop-cli refuses to replace one with the other unless you pass `--replace`.

| Name | skilldrop (pack) | agent-ready-repo (pack) |
|---|---|---|
| `devils-advocate` | Adversarial review of a code change before merge, each bug checked against the code (`dev-team`) | Adversarial review of a research survey or a claim, routing each objection to a verdict (`desk-research`) |
| `file-to-markdown` | Office files, PDFs, web pages and email to Markdown, with images saved and tracked changes kept pending (`converters`) | Documents and images to Markdown for AI context layers, with a stdlib extraction floor (`converters`) |
| `rendering-strategy` | Per-route rendering decision (SSG, ISR, SSR, CSR, edge) from freshness, personalisation, indexing and cost (`frontend`) | Per-route rendering model (CSR, SSR, SSG, ISR, RSC) from data access, performance and personalisation (`frontend-engineering`) |
| `content-design` | A content spec for a page from user needs, with a plain-language rewrite and a readability check (`experience-design`) | What a surface should communicate and how its copy should feel, in three modes up to a brand register (`experience-design`) |
| `information-architecture` | An IA for a product or site: inventory, labels, navigation, sitemap and a tree-test plan (`experience-design`) | What goes where on a screen or flow, including dashboards and reports (`experience-design`) |
| `service-blueprint` | A blueprint from a scenario, with fail points, waits, owners and ranked fixes (`experience-design`) | A blueprint across an existing customer journey's frontstage, backstage and support (`experience-design`) |
| `ux-writing` | A string table for a flow: every string with its context, budget and a variant (`experience-design`) | UI copy voice, recurring state microcopy, and review of copy before it ships (`experience-design`) |

The `devils-advocate` pair does different jobs. For the other six, pick the one whose output you want. Both catalogues also have packs named `core`, `converters` and `experience-design`, with different contents.

## Packs that cover the same work

| Work | skilldrop | agent-ready-repo |
|---|---|---|
| Architecture and decisions | `solution-architect` | `architect`, `repo-governance` |
| Product discovery and strategy | `product-manager` | `product-strategy`, `product-engineering` |
| Building and reviewing code | `dev-team` | `product-engineering`, `code-intelligence` |
| Releasing | `dev-team` (the `release` loop) | `release-engineering` |
| Frontend | `frontend` | `frontend-engineering` |
| Terraform | `infra-as-code` | `iac-terraform` |
| Research with sources | `research` | `desk-research` |
| Trackers | `trackers` (Jira, Linear, GitHub Projects) | `atlassian`, `linear`, `github` |
| Writing skills | `skill-engineering` | `agent-skill-engineering` |
| Figma | `figma-diagrams` in `solution-architect` | `figma` |
| Documentation | `release-notes`, `guide-builder` | `product-documentation` |

## In one catalogue only

- **skilldrop:**
  - operations: `sre-oncall`, `grc`, `data-analytics`;
  - AI work: `ai-engineering`, `api-builder`;
  - communication: `stakeholder-comms`, `design`;
  - roles outside software: `career`, `civil-architect`, `interior-designer`, `event-planner`, `operations-manager`, `educator`, `startup-legal`.
- **agent-ready-repo:** `credential-brokers`, `monorepo-extras`, `catalogue-curation` and `contracts`, plus its own peer-supervised loops and hooks, which install through `agentbundle`.
