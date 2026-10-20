# skilldrop

[![npm](https://img.shields.io/npm/v/skilldrop-cli)](https://www.npmjs.com/package/skilldrop-cli)
[![CLI on Linux, macOS and Windows](https://github.com/sananthanarayan/skilldrop/actions/workflows/cli.yml/badge.svg?branch=main)](https://github.com/sananthanarayan/skilldrop/actions/workflows/cli.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/sananthanarayan/skilldrop/badge)](https://scorecard.dev/viewer/?uri=github.com/sananthanarayan/skilldrop)
[![license](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](LICENSE)

**Agent skills that are measured against the agent without them, and retired when they lose.** Skills for the work people ship: ADRs, PRDs, runbooks, threat models, decks, SQL reviews, DPIAs and Terraform plan reviews. Each one is a folder you copy into Claude Code, Cursor, Kiro, Codex, Antigravity or Copilot.

```bash
npx skilldrop-cli install --pack dev-team     # or product-manager, solution-architect, sre-oncall …
```

## The same request, with and without a skill

From a held-out eval, written blind from the skill's description:

> *"We're taking ClaimLens to the investment committee on Thursday… Can you build a lean canvas for it and set out our riskiest assumptions and how we'd test them?"*

| Plain Claude Code | With [`lean-canvas`](https://sananthanarayan.github.io/skilldrop/skills/lean-canvas/) |
|---|---|
| Finds the corrected break-even (~225 seats), then recommends *"scope the ask to Claims-only Phase 1"*. | *"Corrected, break-even is 225 seats — more than all three departments combined (215), so full rollout still doesn't cover running costs at £40/seat."* |

The blind judge picked the skill's answer: *"A misses this and recommends a Claims-only phase that cannot break even."*

## The receipts

Every skill runs as a real agent session twice: once with the skill, once without. The results are [published either way](https://sananthanarayan.github.io/skilldrop/evals/). In the last full run (5 October 2026: 100 skills, 209 evals, `claude-sonnet-5`):

- **With a skill, answers met 75% of their checks; without one, 44%.** The checks were written by each skill's author, so the fairer number is the next one.
- **Two blind judges preferred the skill's answer in 61% of pairs** (95% interval 55–68%). Each judge saw only the request and both answers, in shuffled order.
- **4 skills that didn't beat the plain agent were [retired](https://sananthanarayan.github.io/skilldrop/evals/#retired)**, and they're listed. Each new skill has to win on held-out evals before it ships.

[Get started](https://sananthanarayan.github.io/skilldrop/start/) · [Browse the packs](https://sananthanarayan.github.io/skilldrop/packs/) · [Search all skills](https://sananthanarayan.github.io/skilldrop/catalogue/) · [Docs](https://sananthanarayan.github.io/skilldrop/docs/) · [Contribute](CONTRIBUTING.md)

## Start in one command

```bash
npx skilldrop-cli install --pack dev-team
```

The install prints a starter prompt for the pack. For `dev-team`, ask your agent:

```text
Is this branch safe to merge? Run a pre-merge review on the current diff.
```

A good result runs your lint, typecheck and tests through a gate script, then a reviewer panel, and ends with `READY` or `NOT READY`. To see any pack's starter, run `npx skilldrop-cli info --pack <name>`.

In Claude Code you can use the plugin marketplace instead: run `/plugin marketplace add sananthanarayan/skilldrop`, then `/plugin install dev-team@skilldrop`. [Every install route](guides/how-to/install.md) covers single skills, other IDEs, loops, reviewer subagents, profiles and updates.

<details>
<summary><b>Choose your role:</b> 19 packs, from product management and architecture to SRE, GRC and job applications</summary>

Install one pack. Every role pack also brings `core` (intake, critique, review council, output hygiene). Each pack page has a starter prompt to paste and says what a good result looks like.

- **Product managers:** `product-manager` — PR/FAQs, strategy, OKRs, business cases, PRDs, success metrics. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/product-manager/)
- **Architects:** `solution-architect` — diagrams, ADRs, design docs, API and data contracts, threat models. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/solution-architect/)
- **Software teams:** `dev-team` — story splitting, implementation with adversarial review, merge gates, PR descriptions, a tech-debt register, launch readiness, release notes. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/dev-team/)
- **SRE and on-call:** `sre-oncall` — observability, runbooks, incident comms, postmortems, capacity. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/sre-oncall/)
- **Explaining things to decision-makers:** `stakeholder-comms` — audience profiles, exec summaries, decision logs, guides. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/stakeholder-comms/)
- **On-brand decks and flyers:** `design` — capture your brand once, then build `.pptx` decks and print-ready flyers with your logo, colours and fonts. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/design/)
- **Adopting and building AI:** `ai-engineering` — readiness, use-case triage, policy, agent loops, budgets, agent threat models, evals. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/ai-engineering/)
- **Building on the Claude API:** `api-builder` — prompt caching, token budgets, eval generation, tool schemas. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/api-builder/)
- **Moving between formats:** `converters` — Markdown to Word, Excel and HTML, files back to Markdown, and Mermaid diagrams checked and rendered. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/converters/)
- **Designing the experience:** `experience-design` — information architecture, UX writing, content design, component specs, service blueprints. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/experience-design/)
- **Researching a question:** `research` — research plans, cited source synthesis, competing hypotheses. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/research/)
- **Keeping the tracker straight:** `trackers` — backlog triage, weekly status from tracker data, briefs turned into issues. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/trackers/)
- **Data and analytics:** `data-analytics` — metric definitions, SQL review, dashboard specs. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/data-analytics/)
- **Governance, risk and compliance:** `grc` — DPIAs, SOC 2 evidence maps, risk registers, security questionnaire answers. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/grc/)
- **Infrastructure as code:** `infra-as-code` — Terraform modules with secure defaults, and plan reviews before apply. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/infra-as-code/)
- **Frontend:** `frontend` — what makes a page slow for real users, what makes a bundle heavy, and how each route should be rendered. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/frontend/)
- **Writing agent skills:** `skill-engineering` — author a portable skill with evals, and review one before it ships. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/skill-engineering/)
- **Applying for a job:** `career` — an honest fit check against the posting, a tailored resume and cover letter that claim nothing you didn't, and the application form's answers. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/career/)
- **Everyone:** `core` on its own. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/core/)

</details>

## How it works

- **A skill produces one file you own.** Each ships a quality bar, named anti-patterns and acceptance evals, so the output is an artifact, not a conversation. See [every skill, by category](guides/reference/skill-catalogue.md).
- **Loops order skills, and a gate decides when work moves on.** Five loops cover the lifecycle (`discover`, `design`, `build`, `release`, `operate`), plus the `ship-a-draft` wrapper for any document and `apply` for a job application. Each gate is a script, a review panel or a person, chosen by how expensive the mistake is to undo. See [the operating model](guides/explanation/operating-model.md) for every stage and gate on one page, [the loops, stage by stage](guides/reference/loops.md), and [why loops](guides/explanation/loops.md).
- **Measured, not asserted.** `run_bench.py` runs each acceptance eval with the skill and without it, in a sandbox, and reports the lift, a blind preference from two judges, and the cost per run. The results are published whether or not they flatter the skills. See [how skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) and [RFC-0040](docs/rfcs/0040-skill-benchmark.md).
- **Copy, never transform.** A skill is a plain `SKILL.md` folder in the [Agent Skills](https://agentskills.io) format, at `packs/<pack>/skills/<name>/`. What runs in your agent is byte-identical to what is reviewed here. There is no runtime, and the tooling has zero dependencies.
- **Updates keep your edits.** `npx skilldrop-cli update` replaces files you haven't touched. For any file you changed, it leaves the new version beside it as `<file>.upstream`. See [upgrade installed skills](guides/how-to/upgrade-skills.md).

## Go deeper

- **Use it:** [the operating model](guides/explanation/operating-model.md) · [docs portal](https://sananthanarayan.github.io/skilldrop/docs/) · [a guide for every pack](guides/README.md#per-pack) · [install in any IDE](guides/how-to/install-per-ide.md) · [try skills in a repo you don't own](guides/how-to/install-per-ide.md#try-skills-in-a-repo-you-dont-own) · [profiles](guides/how-to/profiles.md) · [hooks](guides/how-to/wire-a-hook.md)
- **Run it in CI:** [a skill on every pull request](guides/how-to/run-a-skill-in-ci.md) · [how skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) · [benchmark skills yourself](guides/how-to/benchmark-skills.md) · [measure your loops](guides/how-to/measure-your-loops.md)
- **Roll it out:** [across your org, including an internal mirror](guides/how-to/enterprise-distribution.md) · [publish your own catalogue](guides/how-to/publish-a-catalogue.md) · [security and the OWASP Top 10s](guides/reference/owasp-mapping.md)
- **Reviewers:** three subagents that push back on generated work: `devils-advocate`, `security-reviewer` and `code-quality`. See [`agents/`](agents/README.md).
- **Cost:** each skill declares a provider-neutral model tier (`light`, `standard` or `heavy`). See [MODEL-ROUTING.md](MODEL-ROUTING.md).
- **How it is built:** [ARCHITECTURE.md](ARCHITECTURE.md) · [machine-readable contracts](contracts/) · [decision records](docs/rfcs/) · [`llms.txt`](llms.txt) for tools
- **Contribute:** [CONTRIBUTING.md](CONTRIBUTING.md) · [author a skill](guides/how-to/author-a-skill.md) · [author a loop](guides/how-to/author-a-loop.md) · [repository conventions](AGENTS.md)

## License

MIT or Apache-2.0, at your option. See [LICENSE](LICENSE).
