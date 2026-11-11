# Canary report: home_feed_recs_v2 at 5% (2026-11-07 to 2026-11-10)

Agreed promotion thresholds (from the rollout ticket):
- Home feed error rate at or below 0.5%
- p95 home feed load time at or below 900 ms
- Articles opened per session no lower than 95% of control

| Metric                       | Control (recs-v1) | Canary (recs-v2) |
|------------------------------|-------------------|------------------|
| Home feed error rate         | 0.2%              | 2.1%             |
| p95 home feed load time      | 640 ms            | 870 ms           |
| Articles opened per session  | 3.9               | 4.3              |

Notes: errors in recs-v2 are timeouts, mostly between 19:00 and 22:00,
the evening peak. The cause has not been found yet.
