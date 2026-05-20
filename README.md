# architect-skills

A collection of [Claude Skills](https://code.claude.com/docs/en/skills.md) aimed at making **solution architects** faster on the deliverables they do most: diagrams, design artifacts, and visual specs.

Each skill is self-contained in `skills/<skill-name>/` and follows the standard `SKILL.md` format. The repo is also structured as a Claude Code **plugin** (see `.claude-plugin/plugin.json`), so the whole bundle can be installed in one command.

## Skills in this repo

| Skill | What it does |
|---|---|
| [`architecture-diagrams`](skills/architecture-diagrams/SKILL.md) | Turn a written description of a system into a renderable Mermaid, PlantUML, or C4 diagram. Supports AWS / Azure / GCP cloud shapes, sequence flows, container diagrams, and ER models. |
| [`figma-diagrams`](skills/figma-diagrams/SKILL.md) | Read structure from existing Figma/FigJam files and produce FigJam-importable diagram specs (and comments) via the Figma REST API. Useful when your final deliverable lives in Figma. |

## Try it locally (no install)

From the repo root:

```bash
claude --plugin-dir .
```

Claude will pick up both skills. Then just ask:

> "Draw me a Mermaid diagram of a three-tier web app on AWS with an ALB, two ECS services, and an RDS Postgres backend."

> "Read https://figma.com/file/abc123/MyArchitecture and tell me what frames are in there."

## Install as a plugin

Once this repo is pushed to GitHub:

```
/plugin marketplace add <github-user>/architect-skills
/plugin install architect-skills@<github-user>
```

Skills will then be available as:

- `/architect-skills:architecture-diagrams`
- `/architect-skills:figma-diagrams`

…or invoked automatically by Claude when your prompt matches their descriptions.

## Repo layout

```
architect-skills/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest (name, version, author)
├── skills/
│   ├── architecture-diagrams/
│   │   ├── SKILL.md             # Entry point — short, references other files
│   │   ├── examples/            # Concrete worked examples
│   │   └── templates/           # Reusable Mermaid / PlantUML / C4 starters
│   └── figma-diagrams/
│       ├── SKILL.md
│       ├── reference.md         # Figma REST API quick reference
│       ├── scripts/             # Python helpers Claude invokes via Bash
│       └── templates/
├── README.md
├── LICENSE
└── .gitignore
```

## Adding a new skill

1. Create `skills/<your-skill>/SKILL.md` with this frontmatter:
   ```yaml
   ---
   name: your-skill
   description: One sentence, use-case-first. Claude matches this against user prompts to decide when to invoke.
   ---
   ```
2. Keep `SKILL.md` short (under ~500 lines). Move long reference material into sibling files like `reference.md`, `examples.md`, or `templates/`.
3. If your skill needs scripts, drop them in `scripts/` and invoke them via `${CLAUDE_SKILL_DIR}/scripts/your_script.py` so paths resolve regardless of the user's working directory.
4. Add an entry to the **Skills in this repo** table above.
5. Bump the `version` in `.claude-plugin/plugin.json`.

## Contributing

PRs welcome — especially for new architect-flavoured skills (BPMN, ADR generation, threat-model first drafts, Lucidchart export, etc.). Each new skill should ship with at least one worked example.

## License

MIT — see [LICENSE](LICENSE).
