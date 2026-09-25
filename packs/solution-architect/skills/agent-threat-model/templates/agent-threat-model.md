# Agent threat model — {agent name}

**Modeled:** {YYYY-MM-DD} · **Owner:** {role} · **Input:** {config / design doc / repo}

## Capability inventory

**Data reach** (transitive — what the credentials allow, not what the feature intends)
| Reached via | Data | Scope |
|---|---|---|
| {tool} | {what it can read} | {tenant / repo / global} |

**Content sources**
| Source | Trusted? | Why |
|---|---|---|
| {source} | Untrusted | {every writer who can reach it} |

**Tools** — {list every callable, including read-only ones}

**Egress paths** (swept against the catalog, not just the network tool)
| Channel | Reachable by | Notes |
|---|---|---|
| {channel} | {tool or rendering surface} | {payload capacity} |

## Trifecta matrix

One row per **path**: content source → tools it can influence → egress.

| # | Path | Private data | Untrusted content | Egress | Rank |
|---|---|---|---|---|---|
| 1 | {source} → {tool} → {egress} | ✅ {what} | ✅ {who writes} | ✅ {channel} | 🟥 |
| 2 | … | ✅ | ❌ | ✅ | ⚪ |

## Fixes

### 🟥 Path {#} — {one-line name}

- **Scenario:** {attacker writes X into source → agent reads it → agent calls Y → data lands at Z}
- **Leg broken:** {which one}
- **Change:** {the architectural change, concretely}
- **Verify:** {a config assertion, test, or observed denial a reviewer can run}
- **Residual:** {what is still true after the fix}

## Sweeps

- **Rendered egress:** {finding, or reasoned all-clear}
- **Transitive reach:** {finding, or reasoned all-clear}
- **Inherited capability (subagents / tool-calling tools):** {finding, or reasoned all-clear}

## Residual risk

| Risk | Rank | Accepted by | Revisit when |
|---|---|---|---|
| {what remains} | 🟨 | {named role} | {trigger} |

## Pre-launch checklist

- [ ] {verification per fix above}
- [ ] Egress allowlist enforced and tested with an off-list destination
- [ ] Privileged step accepts structured input only
- [ ] Approval screens show rendered payload and destination
- [ ] Credentials scoped to the narrowest workable reach

**Revisit trigger:** this model is stale the moment a tool, content source, subagent, or credential scope changes.

## Assumptions

- `[assumption]` {what was inferred, and the worst plausible scope it was modeled at}

## Out of scope

- {what this model did not cover, and which skill covers it}
