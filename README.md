# skilldrop

[![npm](https://img.shields.io/npm/v/skilldrop-cli)](https://www.npmjs.com/package/skilldrop-cli)
[![license](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](LICENSE)

**Portable AI-agent skills, measured against the agent without them.** They cover the deliverables knowledge workers actually ship: ADRs, design docs, PRDs, runbooks, threat models, decks, postmortems and adversarial reviews. Each one is a folder you copy into Claude Code, Cursor, Kiro, Codex, Antigravity or Copilot.

```text
messy input → a skill with a quality bar → a gate that can say no → your decision
```

Every skill is run as a real agent session twice, once with the skill and once without, and the results are published either way. [See the numbers and how they were measured](https://sananthanarayan.github.io/skilldrop/evals/).

[Browse the packs](https://sananthanarayan.github.io/skilldrop/packs/) · [Search all skills](https://sananthanarayan.github.io/skilldrop/catalogue/) · [Docs](https://sananthanarayan.github.io/skilldrop/docs/) · [Install options](guides/how-to/install.md) · [Contribute](CONTRIBUTING.md)

## Choose your role

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
- **Writing agent skills:** `skill-engineering` — author a portable skill with evals, and review one before it ships. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/skill-engineering/)
- **Applying for a job:** `career` — an honest fit check against the posting, a tailored resume and cover letter that claim nothing you didn't, and the application form's answers. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/career/)
- **Everyone:** `core` on its own. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/core/)

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

## How it works

- **A skill produces one file you own.** Each ships a quality bar, named anti-patterns and acceptance evals, so the output is an artifact, not a conversation. See [every skill, by category](guides/reference/skill-catalogue.md).
- **Loops order skills, and a gate decides when work moves on.** Five loops cover the lifecycle (`discover`, `design`, `build`, `release`, `operate`), plus the `ship-a-draft` wrapper for any document and `apply` for a job application. Each gate is a script, a review panel or a person, chosen by how expensive the mistake is to undo. See [the loops, stage by stage](guides/reference/loops.md) and [why loops](guides/explanation/loops.md).
- **Measured, not asserted.** `run_bench.py` runs each acceptance eval with the skill and without it, in a sandbox, and reports the lift, a blind preference from two judges, and the cost per run. The results are published whether or not they flatter the skills. See [how skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) and [RFC-0040](docs/rfcs/0040-skill-benchmark.md).
- **Copy, never transform.** A skill is a plain `SKILL.md` folder in the [Agent Skills](https://agentskills.io) format, at `packs/<pack>/skills/<name>/`. What runs in your agent is byte-identical to what is reviewed here. There is no runtime, and the tooling has zero dependencies.
- **Updates keep your edits.** `npx skilldrop-cli update` replaces files you haven't touched. For any file you changed, it leaves the new version beside it as `<file>.upstream`. See [upgrade installed skills](guides/how-to/upgrade-skills.md).

## Go deeper

- **Use it:** [docs portal](https://sananthanarayan.github.io/skilldrop/docs/) · [a guide for every pack](guides/README.md#per-pack) · [install in any IDE](guides/how-to/install-per-ide.md) · [try skills in a repo you don't own](guides/how-to/install-per-ide.md#trying-skills-in-a-repo-you-dont-own) · [profiles](guides/how-to/profiles.md) · [hooks](guides/how-to/wire-a-hook.md)
- **Run it in CI:** [a skill on every pull request](guides/how-to/run-a-skill-in-ci.md) · [how skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) · [benchmark skills yourself](guides/how-to/benchmark-skills.md) · [measure your loops](guides/how-to/measure-your-loops.md)
- **Roll it out:** [across your org, including an internal mirror](guides/how-to/enterprise-distribution.md) · [publish your own catalogue](guides/how-to/publish-a-catalogue.md) · [security and the OWASP Top 10s](guides/reference/owasp-mapping.md)
- **Reviewers:** three subagents that push back on generated work: `devils-advocate`, `security-reviewer` and `code-quality`. See [`agents/`](agents/README.md).
- **Cost:** each skill declares a provider-neutral model tier (`light`, `standard` or `heavy`). See [MODEL-ROUTING.md](MODEL-ROUTING.md).
- **How it is built:** [ARCHITECTURE.md](ARCHITECTURE.md) · [machine-readable contracts](contracts/) · [decision records](docs/rfcs/) · [`llms.txt`](llms.txt) for tools
- **Contribute:** [CONTRIBUTING.md](CONTRIBUTING.md) · [author a skill](guides/how-to/author-a-skill.md) · [author a loop](guides/how-to/author-a-loop.md) · [repository conventions](AGENTS.md)

## License

MIT or Apache-2.0, at your option. See [LICENSE](LICENSE).
