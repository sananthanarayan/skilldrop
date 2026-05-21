# skilldrop

A collection of portable **Claude Skills** you can drop into any IDE — for the deliverables knowledge workers actually ship: diagrams, design docs, ADRs, runbooks, decks, decision logs, comparison matrices, and exec summaries.

Originally scoped to solution architects, now broadly useful to PMs, founders, consultants, engineering leaders, exec assistants — anyone who turns ideas into stakeholder-ready artifacts.

Each skill is a plain directory of `SKILL.md` + supporting files + `manifest.json`. Works in **Claude Code** natively, and ports cleanly to **Cursor**, **Kiro**, **Continue**, **Cline**, **Aider**, and any other AI coding tool that accepts custom instructions or rules.

## Skills in this repo

### Pipeline glue

| Skill | What it does |
|---|---|
| [`brief-intake`](skills/brief-intake/SKILL.md) | Upstream collector. Takes raw mess — a Slack thread, meeting transcript, ticket, email chain, paragraph of notes — and emits a structured brief shaped for whichever downstream skill comes next (ADR, design doc, runbook, exec summary, deck, comparison matrix, decision log). Every field is tagged `[explicit] / [implied] / [inferred] / [missing]` with verbatim quotes from the source. |
| [`doc-critique`](skills/doc-critique/SKILL.md) | Counterpart reviewer. Takes an existing doc (ADR, design doc, runbook, exec summary, comparison matrix, deck, decision log) and produces a structured critique against the same rubrics the generators enforce — verdict + severity-tagged findings (blocker / major / minor / nit) with quoted evidence and concrete fixes, plus a "what's working" section. |

### Dev workflow

| Skill | What it does |
|---|---|
| [`devils-advocate`](skills/devils-advocate/SKILL.md) | Adversarial review of *just-generated* code, run right after an agent (or human) declares a feature done. Sweeps four lenses — edge cases the first pass missed, assumptions baked in that won't survive 6 months, what a staff engineer would push back on in review (concurrency, error handling, security, observability, blast radius), and test-coverage gaps. Produces severity-tagged findings (blocker / major / minor / nit) with file:line evidence, reproducible scenarios, and concrete fixes — plus a "what's solid" section. The code counterpart to `doc-critique`. |

### Diagrams

| Skill | What it does |
|---|---|
| [`architecture-diagrams`](skills/architecture-diagrams/SKILL.md) | Turn a written description of a system into a renderable Mermaid, PlantUML, or C4 diagram. Supports AWS / Azure / GCP cloud shapes, sequence flows, container diagrams, and ER models. |
| [`reverse-architecture`](skills/reverse-architecture/SKILL.md) | Reverse-engineer a system's "as-is" architecture from existing code, IaC (Terraform / CloudFormation / CDK / Pulumi / Bicep), Kubernetes manifests, docker-compose, package manifests, database schema, or OpenAPI. Emits a structured node/edge extraction, a written description suitable for `architecture-diagrams`, and a first-draft Mermaid / C4 diagram with every node tied to a source-of-truth file path. |
| [`figma-diagrams`](skills/figma-diagrams/SKILL.md) | Read structure from existing Figma/FigJam files and produce FigJam-importable diagram specs (and comments) via the Figma REST API. Useful when your final deliverable lives in Figma. |

### Documentation

| Skill | What it does |
|---|---|
| [`adr-generator`](skills/adr-generator/SKILL.md) | Generate an Architecture Decision Record in MADR or Nygard format from a context-decision-consequences brief, with sensible numbering and filename. |
| [`design-doc`](skills/design-doc/SKILL.md) | Generate a Google-style engineering design doc (problem → goals/non-goals → alternatives → proposal → risks → rollout) from a feature brief. |
| [`runbook-generator`](skills/runbook-generator/SKILL.md) | Generate an operational runbook for a service — deploy/rollback, top 5 incident playbooks, SLOs, on-call escalation, dependencies. |
| [`tech-comparison-matrix`](skills/tech-comparison-matrix/SKILL.md) | Produce a weighted comparison matrix for a tech-selection question (e.g. "Postgres vs DynamoDB") with criteria, weights, scores, and a recommendation. |

### AI adoption & observability

| Skill | What it does |
|---|---|
| [`ai-usage-report`](skills/ai-usage-report/SKILL.md) | Turn a CSV/JSONL of AI usage events (exported from an MCP server or other telemetry source) into a per-user, team-rollup, or effectiveness-focused report. Surfaces volume, breadth, session depth, and — where the data supports it — whether AI outputs were actually consumed in shipped artifacts vs generated and discarded (the "AI theater" question). Refuses to generate an aggregate rollup for teams smaller than 5 to preserve anonymity. |

### Stakeholder communication

| Skill | What it does |
|---|---|
| [`audience-profile`](skills/audience-profile/SKILL.md) | Translate an audience type (exec, board, technical, sales, investor, internal, partner, customer) into structural rules — slide count, density, tone, must-have sections. Reusable input for the next three skills. |
| [`slide-outliner`](skills/slide-outliner/SKILL.md) | Outline an architecture-review or pitch deck — slide titles, key points, and speaker notes — sized to a target time budget. Doesn't generate PPTX. |
| [`deck-builder`](skills/deck-builder/SKILL.md) | Generate a real PowerPoint (`.pptx`) file from content + audience + color palette. Uses `python-pptx`; supports 7 layout types and audience-tuned density. Pairs naturally with `audience-profile` + `slide-outliner`. |
| [`exec-summary`](skills/exec-summary/SKILL.md) | Compress a long technical document into a one-page executive summary structured around an Ask, business impact, cost/timeline, risks, and what you need from the audience. |
| [`decision-log`](skills/decision-log/SKILL.md) | Extract decisions, action items, owners, and due dates from meeting notes, Slack threads, or transcripts into a structured log with source attribution. |

## What's in a skill

Every skill folder follows the same layout, so installation is the same anywhere:

```
skills/<skill-name>/
├── SKILL.md              # The instructions the AI agent reads — entry point
├── manifest.json         # Name, description, version, declared deps, required env vars
├── requirements.txt      # (optional) Python deps if the skill has scripts
├── reference.md          # (optional) Long-form reference material
├── examples/             # (optional) Worked examples the agent can study
├── templates/            # (optional) Starter snippets the agent can copy from
└── scripts/              # (optional) Executable helpers the agent invokes
```

The `manifest.json` is the canonical machine-readable summary: its `deps` block lists `pip` / `npm` packages, and `env.required` lists env vars that must be set before the skill works.

## Installing a skill into your IDE

Each skill is a plain directory. Installation is always the same two steps: (1) copy the skill folder into your IDE's skills/rules location, then (2) install the skill's dependencies (the commands are in `manifest.json` under `deps`, or run the install line from the skill's SKILL.md).

### Claude Code

Claude Code reads skills from two locations:

- **User-scope** (available in every project): `~/.claude/skills/<skill-name>/`
- **Project-scope** (tracked with the repo): `<project>/.claude/skills/<skill-name>/`

Install a skill by copying its folder — drop the directory directly into the skills location, **not** its parent category folder:

```bash
# user-scope (recommended for personal use)
mkdir -p ~/.claude/skills
cp -R skills/architecture-diagrams ~/.claude/skills/
cp -R skills/figma-diagrams ~/.claude/skills/

# project-scope (recommended when sharing with a team)
mkdir -p .claude/skills
cp -R skills/architecture-diagrams .claude/skills/
cp -R skills/figma-diagrams .claude/skills/
```

Claude Code discovers the skill via its `SKILL.md` frontmatter `name` field. Invoke it in chat with `/<skill-name>` or by describing the task — Claude will route to the matching skill automatically.

### Cursor

Cursor does not have a native "skills" concept, but you can install a skill as a **project rule**:

1. Copy the skill folder somewhere in the repo (e.g. `.cursor/skills/<skill-name>/`):
   ```bash
   mkdir -p .cursor/skills
   cp -R skills/architecture-diagrams .cursor/skills/
   ```

2. Create `.cursor/rules/<skill-name>.mdc` that points Cursor at it:
   ```markdown
   ---
   description: <paste the skill's description from manifest.json>
   globs:
   alwaysApply: false
   ---
   Follow the instructions in .cursor/skills/<skill-name>/SKILL.md when the user requests this task.
   ```

3. In chat, attach `SKILL.md` with `@` or simply describe the task — the rule will fire when the description matches.

### Kiro

Kiro supports agent instructions via **steering files** and **custom agents**:

1. Copy the skill folder to `.kiro/skills/<skill-name>/`:
   ```bash
   mkdir -p .kiro/skills
   cp -R skills/figma-diagrams .kiro/skills/
   ```

2. Add a steering file at `.kiro/steering/<skill-name>.md` that tells Kiro to defer to the skill's `SKILL.md` when the matching task is requested.

3. Alternatively, paste the contents of `SKILL.md` directly into a custom Kiro agent definition — this is cleaner if you want the skill to be one-click-invocable.

### Continue, Cline, Aider, and other agents

These tools don't have a standard skills directory yet. Two patterns work:

- **Context attachment.** Copy the skill folder anywhere in the repo, then attach `SKILL.md` to your prompt (Continue: `@file`, Cline: `@file`, Aider: `/add <path>`) and tell the agent to follow it.
- **Custom prompt / agent.** Paste `SKILL.md` into the IDE's custom-agent or system-prompt configuration. The skill's `manifest.json` `description` field is a good seed for the agent's name/summary.

In all cases, the scripts are invoked from the **copied** folder, so keep the directory structure intact — don't flatten `scripts/` or `templates/` out of the skill folder.

### VS Code (Continue / Cline extensions)

These behave like the "Other agents" path above. For Continue, you can also add the skill folder to `.continue/config.json` under `contextProviders` so `SKILL.md` shows up in `@` suggestions.

## Installing dependencies

Each skill declares its deps in `manifest.json`:

- **`deps.npm`** → run `npm install <packages>` before using the skill (or let `SKILL.md` step 1 install them on demand).
- **`deps.pip`** → run `python3 -m pip install -r <skill>/requirements.txt`.

Per-skill quick reference:

| Skill | Install command (run from inside the copied skill folder) |
|---|---|
| `figma-diagrams` | `python3 -m pip install -r requirements.txt` + `export FIGMA_TOKEN=figd_...` |
| `deck-builder` | `python3 -m pip install -r requirements.txt` (installs `python-pptx`) |
| _all other skills_ | _no runtime deps — pure markdown skills_ |

For `figma-diagrams`, you also need a [Figma Personal Access Token](https://www.figma.com/developers/api#access-tokens) exported as the `FIGMA_TOKEN` env var.

## Skill Usage

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

## Adding a new skill

1. Create `skills/<your-skill>/SKILL.md` with this frontmatter:
   ```yaml
   ---
   name: your-skill
   description: One sentence, use-case-first. AI agents match this against user prompts to decide when to invoke.
   ---
   ```
2. Add `skills/<your-skill>/manifest.json` with the same `name` + `description` plus declared `deps` and required env vars — this is what makes the skill portable across IDEs.
3. Keep `SKILL.md` short (under ~500 lines). Move long reference material into sibling files like `reference.md`, `examples.md`, or `templates/`.
4. If your skill needs scripts, drop them in `scripts/` and reference them with a path relative to the skill folder — **avoid hard-coding `${CLAUDE_SKILL_DIR}` only**; show both paths so non–Claude-Code users aren't stuck.
5. Add an entry to the **Skills in this repo** table above and to the **Installing dependencies** table.

## Contributing

PRs welcome — especially for new architect-flavoured skills (BPMN, threat-model first drafts, Lucidchart export, draw.io XML, capacity / napkin-math estimation, etc.). Each new skill should ship with at least one worked example and a populated `manifest.json`.

**Workflow in one sentence:** fork or branch off `main` → push to a feature branch → open a PR → a maintainer reviews, approves, and merges. **Contributors:** no direct commits to `main`; only maintainers can approve and merge. **Maintainers** default to the same workflow, with a documented [bypass](CONTRIBUTING.md#maintainer-bypass-when-direct-commits-are-ok) for trivial / urgent changes. Maintainers are listed in [MAINTAINERS.md](MAINTAINERS.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide — branching & merge policy, anatomy of a skill, voice & tone, the PR checklist, and rules for adding a new README section.

## License

MIT — see [LICENSE](LICENSE).
