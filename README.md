# skilldrop

[![npm](https://img.shields.io/npm/v/skilldrop-cli)](https://www.npmjs.com/package/skilldrop-cli)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Portable AI-agent skills for the deliverables knowledge workers actually ship:** ADRs, design docs, PRDs, runbooks, threat models, decks, postmortems and adversarial reviews. Each one is a folder you copy into Claude Code, Cursor, Kiro, Codex or Copilot.

```text
messy input → a skill with a quality bar → a gate that can say no → your decision
```

[Browse the packs](https://sananthanarayan.github.io/skilldrop/packs/) · [Search all skills](https://sananthanarayan.github.io/skilldrop/catalogue/) · [Docs](https://sananthanarayan.github.io/skilldrop/docs/) · [Install options](guides/how-to/install.md) · [Contribute](CONTRIBUTING.md)

## Choose your role

Install one pack. Every role pack also brings `core` (intake, critique, review council, output hygiene). Each pack page has a starter prompt to paste and says what a good result looks like.

- **Product managers:** `product-manager` — PR/FAQs, strategy, OKRs, business cases, PRDs, success metrics. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/product-manager/)
- **Architects:** `solution-architect` — diagrams, ADRs, design docs, API and data contracts, threat models. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/solution-architect/)
- **Software teams:** `dev-team` — story splitting, implementation with adversarial review, merge gates, launch readiness, release notes. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/dev-team/)
- **SRE and on-call:** `sre-oncall` — observability, runbooks, incident comms, postmortems, capacity. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/sre-oncall/)
- **Explaining things to decision-makers:** `stakeholder-comms` — audience profiles, exec summaries, decision logs, guides. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/stakeholder-comms/)
- **On-brand decks and flyers:** `design` — capture your brand once, then build `.pptx` decks and print-ready flyers with your logo, colours and fonts. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/design/)
- **Adopting and building AI:** `ai-engineering` — readiness, use-case triage, policy, agent loops, budgets, agent threat models, evals. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/ai-engineering/)
- **Building on the Claude API:** `claude-api` — prompt caching, token budgets, eval generation, tool schemas. [Open pack](https://sananthanarayan.github.io/skilldrop/packs/claude-api/)
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
- **Loops order skills, and a gate decides when work moves on.** Five loops cover the lifecycle (`discover`, `design`, `build`, `release`, `operate`), plus the `ship-a-draft` wrapper for any document. Each gate is a script, a review panel or a person, chosen by how expensive the mistake is to undo. See [the loops, stage by stage](guides/reference/loops.md) and [why loops](guides/explanation/loops.md).
- **Copy, never transform.** A skill is a plain `SKILL.md` folder in the [Agent Skills](https://agentskills.io) format, at `packs/<pack>/skills/<name>/`. What runs in your agent is byte-identical to what is reviewed here. There is no runtime, and the tooling has zero dependencies.
- **Updates keep your edits.** `npx skilldrop-cli update` replaces files you haven't touched. For any file you changed, it leaves the new version beside it as `<file>.upstream`. See [upgrade installed skills](guides/how-to/upgrade-skills.md).

## Go deeper

- **Use it:** [docs portal](https://sananthanarayan.github.io/skilldrop/docs/) · [install in any IDE](guides/how-to/install-per-ide.md) · [profiles](guides/how-to/profiles.md) · [hooks](guides/how-to/wire-a-hook.md) · [publish your own catalogue](guides/how-to/publish-a-catalogue.md)
- **Reviewers:** three subagents that push back on generated work: `devils-advocate`, `security-reviewer` and `code-quality`. See [`agents/`](agents/README.md).
- **Cost:** each skill declares a provider-neutral model tier (`light`, `standard` or `heavy`). See [MODEL-ROUTING.md](MODEL-ROUTING.md).
- **How it is built:** [ARCHITECTURE.md](ARCHITECTURE.md) · [machine-readable contracts](contracts/) · [decision records](docs/rfcs/) · [`llms.txt`](llms.txt) for tools
- **Contribute:** [CONTRIBUTING.md](CONTRIBUTING.md) · [author a skill](guides/how-to/author-a-skill.md) · [author a loop](guides/how-to/author-a-loop.md) · [repository conventions](AGENTS.md)

## License

MIT — see [LICENSE](LICENSE).
