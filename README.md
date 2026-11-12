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

> *"Our design agency sent the Figma file for Ostwick Museum's new signage as a JSON export… Can you (1) list the pages and the frames on each, (2) check the Final page against what the Brief page asks for, and (3) draft the comments I should leave for the agency on any frames with problems — one line each."*

| Plain Claude Code | With [`figma-diagrams`](https://sananthanarayan.github.io/skilldrop/skills/figma-diagrams/) |
|---|---|
| Finds the same three problems, then drafts comments of two sentences or more, and adds a fourth one about the Archive page that the file doesn't support. | *"The cover email is wrong on both counts. The Sign Types page has 11 frames, not 12, and Type 07 is missing."* Then one line per frame with a problem. |

Both blind judges picked the skill's answer: *"A keeps each comment to a single sentence as asked, while B's main comments run to two sentences and its fourth comment is speculative."*

## The receipts

Every skill runs as a real agent session twice: once with the skill, once without. The results are [published either way](https://sananthanarayan.github.io/skilldrop/evals/). In the latest run (5 November 2026: 111 skills, 300 held-out evals written blind from each skill's description, `claude-sonnet-5-5`, scripts free to run):

- **With a skill, answers met 84% of their checks; without one, 76%.**
- **Two blind judges preferred the skill's answer in 44% and 42% of pairs.** Each judge saw only the request and both answers, in shuffled order. Skills that ship a script came out slightly ahead of the plain agent (52%); skills that are instructions alone lost about two pairs in three ([what the benchmark showed](guides/explanation/what-the-benchmark-showed.md#a-new-baseline-with-scripts-free-to-run)).
- **Loops are measured against their own skills, used without the loop.** On fresh held-out evals the 11 loops were preferred to plain Claude Code in 65% and 70% of pairs, and came out even with their own skills (52% and 59%). Clearly ahead of their skills: [`ship-agent`](packs/ai-engineering/loops/ship-agent/LOOP.md), [`clarify`](packs/experience-design/loops/clarify/LOOP.md) and [`provision`](packs/infra-as-code/loops/provision/LOOP.md). [`build`](packs/dev-team/loops/build/LOOP.md) and [`design`](packs/solution-architect/loops/design/LOOP.md) lost to theirs twice, and were rebuilt to beat them ([RFC-0084](docs/rfcs/0084-build-and-design-rebuilt.md)). Four that lost to their skills were retired ([RFC-0074](docs/rfcs/0074-loops-measured-four-retired.md), [RFC-0083](docs/rfcs/0083-loop-replies-in-plain-words.md)).
- **Ten skills and four loops that didn't beat the alternative were [retired](https://sananthanarayan.github.io/skilldrop/evals/#retired)**, and they're listed. Each new skill has to win on held-out evals before it ships.

[Get started](https://sananthanarayan.github.io/skilldrop/start/) · [Browse the packs](https://sananthanarayan.github.io/skilldrop/packs/) · [Search all skills](https://sananthanarayan.github.io/skilldrop/catalogue/) · [Docs](https://sananthanarayan.github.io/skilldrop/docs/) · [What stays stable in 1.x](guides/reference/versioning-and-stability.md) · [Contribute](CONTRIBUTING.md)

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
<summary><b>Choose your role:</b> 25 packs, from product management and architecture to SRE, GRC, job applications, building design, startup legal and teaching</summary>

Install one pack. Every role pack also brings `core` (intake, critique, review council, output hygiene, and the decisions behind a codebase). Each pack page has a starter prompt to paste and says what a good result looks like.

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
- **Researching a question:** `research` — research plans, cited source synthesis, competing hypotheses, and a manuscript's citations and cross-references checked before submission. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/research/)
- **Keeping the tracker straight:** `trackers` — backlog triage, weekly status from tracker data, briefs turned into issues. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/trackers/)
- **Data and analytics:** `data-analytics` — metric definitions, SQL review, dashboard specs. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/data-analytics/)
- **Governance, risk and compliance:** `grc` — DPIAs, SOC 2 evidence maps, risk registers, security questionnaire answers. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/grc/)
- **Infrastructure as code:** `infra-as-code` — Terraform modules with secure defaults, and plan reviews before apply. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/infra-as-code/)
- **Frontend:** `frontend` — what makes a page slow for real users, what makes a bundle heavy, and how each route should be rendered. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/frontend/)
- **Writing agent skills:** `skill-engineering` — author a portable skill with evals, and review one before it ships. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/skill-engineering/)
- **Applying for a job:** `career` — an honest fit check against the posting, a tailored resume and cover letter that claim nothing you didn't, and the application form's answers. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/career/)
- **Designing buildings:** `civil-architect` — a dimensioned concept floor plan from a room list and a footprint, checked for overlapping rooms, doors on no wall and rooms no one can reach. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/civil-architect/)
- **Running a team on shifts:** `operations-manager` — a weekly rota checked for cover, hours, rest between shifts and days in a row, handed back in your own sheet. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/operations-manager/)
- **Running events:** `event-planner` — a seating plan where every together, keep-apart and access request holds, and a run of show with no room or person booked twice, both checked and drawn. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/event-planner/)
- **Furnishing rooms:** `interior-designer` — a dimensioned furniture plan for one room, checked for door swings, bed and chair clearances, a clear route to everything and turning space where it's required. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/interior-designer/)
- **Startup founders:** `startup-legal` — an agreement checked before you sign it, with wording to push back on, your cap table through SAFEs and a priced round, vesting with the 83(b) deadline, and your first office lease's real cost and exit dates. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/startup-legal/)
- **Teachers:** `educator` — an exam paper and its mark scheme checked before printing: totals that add up, parts the scheme misses or marks differently, and balance across objectives. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/educator/)
- **Everyone:** `core` on its own. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/core/)

</details>

## How it works

- **A skill produces one file you own.** Each ships a quality bar, named anti-patterns and acceptance evals, so the output is an artifact, not a conversation. See [every skill, by category](guides/reference/skill-catalogue.md).
- **Loops order skills, and a gate decides when work moves on.** Loops cover three lifecycle stages (`design`, `build`, `release`), plus the `ship-a-draft` wrapper for any document and loops for jobs beside it, such as `research`, `comply`, `ship-agent` for an AI agent and `provision` for a Terraform change. Every loop is measured against its own skills used without it; four that lost were retired. Each gate is a script, a review panel or a person, chosen by how expensive the mistake is to undo. See [the operating model](guides/explanation/operating-model.md) for every stage and gate on one page, [the loops, stage by stage](guides/reference/loops.md), and [why loops](guides/explanation/loops.md).
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
