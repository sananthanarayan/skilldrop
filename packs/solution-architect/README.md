# Solution architect

Design-phase artifacts: diagrams, decision records, design docs, contracts, schemas, threat models, and the reviews that gate them.

`/plugin install solution-architect@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Record an architecture decision your team already made

Paste this into Claude Code:

```text
Write an ADR: we're moving our session store from Redis to DynamoDB. We considered staying on Redis, DynamoDB, and Postgres; we chose DynamoDB for managed scaling and lower ops load.
```

- **How to tell it worked:** adr-generator returns an ADR with context, the options considered with their trade-offs, the decision, and its consequences.
- **If nothing happens:** If adr-generator does not activate, ask for it by name ("use adr-generator") and check that its folder exists in your skills folder (`~/.claude/skills/` by default).

## Loops

- `ship-a-draft`
- `design`

## Skills

- `adr-generator`
- `api-contract-draft`
- `architecture-diagrams`
- `brief-intake`
- `council-review`
- `data-contract`
- `db-schema-design`
- `design-doc`
- `doc-critique`
- `figma-diagrams`
- `nfr-spec`
- `output-hygiene`
- `reverse-architecture`
- `tech-comparison-matrix`
- `threat-model`

More: https://sananthanarayan.github.io/skilldrop/packs/solution-architect/
