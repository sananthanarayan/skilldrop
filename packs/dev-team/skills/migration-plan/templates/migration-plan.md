# Migration-plan template

Overview table first; per-phase detail second. Every phase carries the four mandatory fields — a phase missing one isn't done being planned.

```markdown
# Migration plan: {current state} → {target state}

**Done means:** {checkable end state — "all reads on v2, v1 returns 410, legacy table dropped"}
**Constraints:** downtime tolerance: {zero | window}; data volume: {rows/GB}; deadline: {date or none}
[assumption] {defaults picked; one line each}

## Phase overview

| # | Phase | Change (one only) | Gate (observable) | Bake | Rollback | Blast radius |
|---|---|---|---|---|---|---|
| 1 | Expand schema | schema | migration applied, no slow-query regression | 24h | drop column (unused) | none — additive |
| 2 | Dual-write | code path | write-error rate ≤ baseline; reconciler green | 48h | flag off, single-write | writes |
| 3 | Backfill | data | parity 3-depth pass | — | stop job (resumable) | none — old path authoritative |
| 4 | Ramp reads | traffic | per-step thresholds below | per step | flag to 0% | readers at current % |
| 5 | **Point of no return:** {e.g. new store authoritative} | authority | {pre-crossing checklist} | — | **none — see below** | all |
| 6 | Contract | cleanup | zero old-path reads for 14d | — | n/a (old path already cold) | none |

## Per-phase detail

### Phase {n} — {name}

- **Action:** {exactly one change}
- **Gate:** {metric + threshold + duration; who checks; dashboard link placeholder}
- **Rollback:** {steps; data story explicitly — what happens to writes made since the phase started}
  - Rehearsed: {date/environment, or "scheduled for {date}"}
- **Blast radius:** {affected users/systems if this phase fails mid-way}
- **Comms:** {who is told what, or "silence — deliberate, because {reason}"}

## Backfill spec

- **Idempotent:** {why re-running is safe — upsert keying, version guard}
- **Resumable:** {checkpoint mechanism + granularity}
- **Rate limit:** {N/s, and the metric that triggers slowdown — e.g. replica lag > 5s}
- **Parity verification:**
  1. Counts: {per table/partition}
  2. Aggregates/checksums: {per partition, scheduled}
  3. Deep-compare: {sample size + field-level diff}
- **Dual-write reconciler:** {job name, schedule, alert on divergence > {threshold}} — required whenever dual-write is on

## Traffic ramp

| Step | Share | Min duration | Abort threshold |
|---|---|---|---|
| canary | internal / 1% | 24h | any correctness diff |
| 2 | 10% | 24h | error rate > baseline +0.1% |
| 3 | 50% | 48h | p99 > {x} ms |
| 4 | 100% | 7d before phase 5 | — |

## Point of no return

**Crossing:** {the action after which rollback is impossible}
**Verify immediately before:** {checklist}
**Sign-off:** {role}

## Contract phase commitment

- Remove: {flags, dual-write, legacy tables/endpoints}
- Owner: {role} · Date: {YYYY-MM-DD} · Gate: {e.g. zero old-path reads 14d, verified by metric}

## Open assumptions / questions

- [assumption] {…} — confirm with {who}
```
