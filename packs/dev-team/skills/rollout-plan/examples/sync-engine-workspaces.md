# Example — new sync engine, ramped by workspace

A worked input → output. The company, product and numbers are fictional.

## Input

> Fieldnote is moving note sync to the new engine behind the flag `sync_v2`, evaluated
> server-side per workspace. Desktop and mobile 3.4 contain both engines; the server tells each
> client which to use. About 20,000 sync sessions an hour on average, peaking at 34,000 around
> 10:00 UTC on weekdays. Sync failure rate is 1.2% of sessions; p95 sync latency is 900 ms.
> Notes edited under `sync_v2` are stored in a new op-log format that the old engine can't read
> until `oplog_export` converts them back (about 1 second per note). Business-plan workspaces
> have a 99.9% sync availability SLA. A pricing experiment runs on 10% of Free workspaces until
> 30 Oct. Plan the rollout.

## Working (not shown in the reply)

```bash
python3 scripts/canary_math.py --baseline 1.2% --detect-abs 0.3pp --traffic 20000 --unit sessions --steps 1,5,25,50,100
```

| Exposure | Treatment sessions needed | Minimum time | Status |
|---|---|---|---|
| 1% | 11,199 | 56.0 h | ok |
| 5% | 11,718 | 11.7 h | ok |
| 25% | 15,137 | 3.0 h | ok |
| 50% | 23,228 | 2.3 h | ok |
| 100% | — | n/a | no concurrent control |

## Output

**Internal → 1% → 5% → 25% → 50% → 100% over about 7 days. The real risk is the rollback, not
the ramp: every note edited under the new engine needs converting back before the old engine can
read it, so each step makes turning the flag off slower.**

**Binding constraint:** rollback cost, which grows with every note edited on `sync_v2`; traffic is
high enough for the default ladder. At 20,000 sessions an hour and a 1.2% failure rate, even 1% sees
a 0.3 pp rise in about 2.5 days, so no step is crash-only. The pricing experiment holds its
workspaces out until 30 Oct.

Assumptions: the smallest regression worth catching is +0.3 pp in sync failures `[assumption]`;
the flag stays per workspace, so every member of a workspace is on one engine.

### Metrics

All thresholds compare flag-on workspaces with flag-off workspaces in the same hours.

| Metric | Role | Baseline | Threshold | Abort (any time) |
|---|---|---|---|---|
| Sync failure rate (share of sessions) | decision | 1.2% | ≤ control + 0.3 pp | > 3× control for 10 min |
| p95 sync latency | guardrail | 900 ms | ≤ control + 150 ms `[assumption]` | > control + 2 s for 10 min |
| p99 sync latency | guardrail | to confirm | ≤ control + 400 ms `[assumption]`, read at 10,000+ sessions per arm | |
| Op-log conversion backlog | guardrail | none today | `oplog_export` dry-run on the step's notes finishes inside 1 h | |

Session counts overstate the evidence: sessions from one workspace are correlated, so the
times below are floors.

### Ladder

| Step | Exposure | Who and why | Minimum time | Can catch |
|---|---|---|---|---|
| 0 | internal | Fieldnote's own workspaces: crashes and format bugs at no customer cost | 24 h | crashes only |
| 1 | 1% | Free and Pro workspaces by `hash(salt + workspace_id)`; excludes Business (SLA) and the pricing-experiment workspaces | 56 h (covers two weekday 10:00 peaks) | ≥ 0.3 pp |
| 2 | 5% | same rule, nested | 24 h (one full peak; statistics need 11.7 h) | ≥ 0.3 pp |
| 3 | 25% | same rule; pricing-experiment workspaces join after 30 Oct | 24 h | ≥ 0.3 pp |
| 4 | 50% | Business workspaces join here | 24 h | ≥ 0.3 pp |
| 5 | 100% | everyone; 2% holdback of Free workspaces kept 7 days for the failure-rate comparison | 7 days | holdback only |

### Step rules

- **Promote** when the minimum time is reached and every guardrail is inside its threshold.
- **Hold** for one extension of 24 h if the failure rate sits between threshold and abort; still there → roll back.
- **Roll back** on any threshold breach at the planned sample, or any abort.
- **Abort:** automated if the flag service can turn `sync_v2` off on a metric (to confirm); otherwise manual, with the abort rule as a page to sync on-call.
- **Watcher:** sync on-call. **Override:** only the sync engineering lead may promote past a breach, with the reason in the rollout channel.

### Rollback

**Flag off:** sync on-call, in the flag service; clients switch engine at their next sync.

| Category | What this change does | Undone by flag-off? | Handling |
|---|---|---|---|
| Data written in a new format | Notes edited under `sync_v2` are stored as op-log | **no** | Turn the flag off, then run `oplog_export` on the flag-on workspaces at once; their v2-edited notes stay unreadable to the old engine until it finishes. Rehearse it on step 0 data |
| Caches | Clients cache the engine choice until next sync | yes, at next sync | none |
| Clients already shipped | 3.4 clients carry both engines; the server chooses | yes | Clients older than 3.4 never get `sync_v2`, verified at step 0 |

**Point of no return:** none, provided `oplog_export` is rehearsed. The cost of going back grows
with every step: at about 1 second per note, rolling back 50% of workspaces takes as long as
converting every note they have edited since step 1. Before step 4, time the conversion on the
step 3 cohort and hold if it exceeds 1 hour.

### Flag removal

- **Owner:** sync engineering lead · **Date:** 30 days after 100% · **Gate:** 100% for 14 days, no rollback.
- **Removes:** the `sync_v2` flag, the old sync engine on the server, `oplog_export` once no old-format reader remains, and the flag's dashboard.
- **Clients:** the old engine leaves the apps in the first release after removal; the server path stays until 3.4 is the minimum supported version.

### To confirm

- p99 sync latency baseline.
- How many notes an average workspace edits per day, to size the rollback time at each step.
- Whether the flag service can turn the flag off automatically on a metric, or only on a manual flip.
