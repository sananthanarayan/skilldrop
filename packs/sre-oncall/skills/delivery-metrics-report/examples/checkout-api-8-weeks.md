# Example: checkout-api, 8 weeks

Northwind's checkout team exported eight weeks of data (2026-07-06 to 2026-08-30) and asked: "Compute our DORA metrics and tell us what changed."

## Input

Three files in this folder (synthetic data, made-up names):

- [`deployments.csv`](deployments.csv): 48 rows. 40 are checkout-api production deploys in the window. The rest are a staging deploy, a production row with an empty `deployed_at`, and 6 search-api deploys. Timestamps mix `Z` and `+01:00`.
- [`incidents.csv`](incidents.csv): 6 incidents. Two name the deploy that caused them, one is unresolved, and one belongs to search-api.
- [`prs.csv`](prs.csv): 83 PRs with `first_commit_at`: 79 linked to a deploy by `deploy_id`, and four that never merged: three still open and one closed unmerged.

The user named the service and the window, so no questions were needed.

## Command

```bash
python3 scripts/delivery_metrics.py \
  --deployments examples/deployments.csv --incidents examples/incidents.csv --prs examples/prs.csv \
  --service checkout-api --from 2026-07-06 --to 2026-08-30 --json out/metrics.json
```

## Script output (real, unedited)

```markdown
# Delivery metrics: checkout-api

Window: 2026-07-06 to 2026-08-30 (56 days). Weeks: ISO weeks starting Monday, UTC.

## DORA software delivery metrics

| Metric | Value |
|---|---|
| Deployment frequency | 40 deployments; 5.00 per week; deployed on 34 of 56 days (60.7%) |
| Change fail rate | 5 of 40 deployments (12.5%) |
| Deployment rework rate | 4 of 40 deployments (10.0%) |

| Duration metric | n | p50 | p85 | p95 | Measured |
|---|---|---|---|---|---|
| Lead time for changes | 79 | 36.3 h | 2.6 d | 3.2 d | prs.first_commit_at -> deployed_at of prs.deploy_id |
| Failed deployment recovery time | 5 (low n) | 54 min | 23.8 h | 43.2 h | failed deploy -> recovered |
| Time to restore service (all incidents) | 4 (low n) | 1.6 h | 3.2 h | 3.6 h | incident start -> resolved |

## Weekly series

| Week of | Deploys | Failed | Fail rate | Merged | WIP at week end |
|---|---|---|---|---|---|
| 2026-07-06 | 3 | 0 | 0.0% | 4 | 2 |
| 2026-07-13 | 3 | 1 | 33.3% | 5 | 3 |
| 2026-07-20 | 4 | 0 | 0.0% | 9 | 3 |
| 2026-07-27 | 4 | 0 | 0.0% | 10 | 6 |
| 2026-08-03 | 6 | 4 | 66.7% | 9 | 3 |
| 2026-08-10 | 6 | 0 | 0.0% | 11 | 2 |
| 2026-08-17 | 7 | 0 | 0.0% | 13 | 3 |
| 2026-08-24 | 7 | 0 | 0.0% | 18 | 3 |

## Flow

| Measure | Value |
|---|---|
| Cycle time p50 / p85 | 34.6 h / 2.5 d (n=79; earlier of first_commit_at and opened_at -> merged) |
| Throughput | 9.88 merged per week |
| Abandoned (closed unmerged) in window | 1 |

## Data quality

- deploy rows read: 48
- deploy rows skipped missing deployed at: 1
- deploy rows skipped non production: 1
- incident rows read: 6
- incidents unresolved excluded from restore time: 1
- incident rows skipped missing started at: 0
- prs without a deploy in window or first commit: 4
- timestamps with assumed offset: 0

Percentiles use linear interpolation between ranks. "low n" means fewer than 10 observations.
```

Excerpt of the JSON written to `--json`:

```json
{
  "change_fail_rate": {
    "failed_deployments": 5,
    "deployments": 40,
    "rate": 0.125
  },
  "failed_deployment_recovery_time": {
    "n": 5,
    "p50_hours": 0.9,
    "p85_hours": 23.8,
    "p95_hours": 43.17,
    "low_n": true
  }
}
```

## Interpretation the skill writes from that output

**Scope:** checkout-api, production only, 8 ISO weeks. DORA's current metric names, as defined at dora.dev. Time to restore service across all incidents is context only.

**Summary.** Deployments more than doubled, from 3 a week in July to 7 a week by late August, and change fail rate stayed at 0% in every week except two. The week of 2026-08-03 had 4 failed deploys out of 6, and on its own it accounts for most of the 12.5% overall rate. Find out what changed that week before treating 12.5% as the baseline.

**Findings**

1. **Throughput rose without a lasting loss of stability.** Weekly deploys went 3, 3, 4, 4, 6, 6, 7, 7. Six of the eight weeks had no failed deploy. Merged PRs per week rose from 4 to 18. **Next check:** confirm the rise came from smaller changes rather than more people. Compare PRs per deploy (79 PRs linked across 40 deploys).
2. **The week of 2026-08-03 is the outlier: 4 of 6 deploys failed.** Three were rolled back (dep-1056, dep-1058, dep-1060), and dep-1055 caused INC-318, a SEV1. **Next check:** what was deployed or changed in the pipeline that week. Hand INC-318 to `postmortem-generator` if it has no write-up.
3. **Recovery is fast when a failure is caught, and slow when it isn't.** Failed deployment recovery time p50 is 54 min, but p85 is 23.8 h. The three rollbacks recovered in under an hour, and the hotfix (dep-1046) in about 4.4 h. dep-1055 ran for about two days before INC-318 opened and was resolved. With n = 5 the percentiles are not stable. The pattern points at detection, not at the rollback process. **Next check:** why nothing alerted between the 2026-08-03 deploy and the 2026-08-05 incident. That is an `observability-plan` question.
4. **Most lead time is before merge, not after.** Change lead time p50 is 36.3 h against cycle time p50 of 34.6 h, so merged changes reach production within a couple of hours. Shortening lead time further means smaller PRs or faster review, not pipeline work.
5. **WIP is steady at 2 to 3 except a spike to 6 in the week of 2026-07-27.** Throughput did not fall that week (10 merged), so the spike looks like a batch of work starting, not a blockage.

**Data gaps**

- 1 production row skipped because `deployed_at` is empty (dep-1999). Fix it at the source.
- INC-327 is unresolved, so it is left out of the restore time.
- 4 PRs have no deploy, so they are not in lead time: 3 are still open and 1 was closed unmerged.
- Failed deployment recovery time (n = 5) and all-incident restore time (n = 4) are low n.

**What to measure next:** set `caused_by_deploy` on every incident. Two of the four resolved checkout-api incidents have no link, so change fail rate may be undercounted.

## What the skill declined

The user then asked: "Is 12.5% better than the search team's?" The skill replied that DORA metrics are meant per service and for a team improving against its own history. It added that search-api's deploys and failures may be defined differently, and that a cross-team ranking would push both teams toward gaming the numbers. It offered to run search-api's own 8-week trend with the same definitions instead.
