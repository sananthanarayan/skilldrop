# Orchestration plan: {task}

> Fan-out justification: {context separation | independence | role conflict} — {one line why}. If none applies, this document should instead say: use one agent.

## Role cards

### {agent-name}
- **Mission:** {one sentence, one job, no "and"}
- **Inputs:** {exactly what it receives}
- **Denied (isolation):** {what it must not see, and why}
- **Output contract:** `{ field: type, field: type }` — schema, not prose
- **Tools/permissions:** {least privilege}
- **On failure:** {structured BLOCKED/empty return — never improvisation}
- **Tier:** {light | standard | heavy} — {why this tier suffices}

<!-- one card per agent role (use ×N in the name for a mission repeated per item), and always include a card for the orchestrator itself -->

## Topology

**Shape:** {pipeline | parallel+barrier | judge panel} — **because** {the named dependency or independence requirement}.
{If barrier: the cross-item dependency that earns it. If judge panel: the vote rule.}
**Depth:** one level. {Justification here if any agent spawns agents.}

```mermaid
flowchart LR
    O[orchestrator] --> A[{agent}]
    O --> B[{agent}]
    A --> V{verify}
    B --> V
    V -->|pass| OUT[{artifact}]
    V -->|refuted| F[failure route]
```

## Aggregation & verification

- **Aggregation:** {code-shaped merge — dedup key, schema union}; contract-invalid output → failure route, never the merge
- **Verification:** {adversarial verifier — persona/prompt, independent of all generators}; verdict gates the result
- **Vote rule:** {panels: e.g. finding survives unless 2 of 3 refute · single verifier: "ships unless refuted"}

## Budget line

Fleet cap per run: {tokens/currency} `[source: agent-budget spec | assumption]` · Worker tiers as carded above · On cap: {stop and escalate — see the loop spec}

## Hand-offs

- Loop wrapping this fan-out (caps, gates, exits) → `agent-loop-design`
- Full spend model → `agent-budget`
