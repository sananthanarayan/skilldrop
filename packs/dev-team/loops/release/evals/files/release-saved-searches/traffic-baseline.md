# Search traffic baseline (last 28 days, to 2 Nov 2026)

Source: https://grafana.example/d/search-overview (pulled by Kofi, 3 Nov)

| Metric | Value |
|---|---|
| Weekly active users (all of Tallyhall) | ~18,000 |
| Daily users who run at least one search | ~2,600 (weekdays); ~400 (weekends) |
| Searches per day | ~31,000 (weekdays) |
| Search API p95 latency | 420 ms |
| Search API p99 latency | 1.1 s |
| Search API 5xx rate | 0.3% |
| Searches repeated by the same user within 7 days (same query text) | 38% |

## Cohorts available for flag targeting

| Cohort | Size |
|---|---|
| Internal staff (Tallyhall workspace) | 140 users |
| Design partners (opted in to early access) | 9 workspaces, ~600 users |
| Everyone else | percentage rollout by workspace ID |

Flag tool supports targeting by cohort and by percentage of workspaces. It does not support percentage of users within a workspace.
