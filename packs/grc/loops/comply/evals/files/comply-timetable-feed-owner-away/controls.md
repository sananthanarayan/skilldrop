# Controls

| Id | Control | Evidence |
|---|---|---|
| C1 | Feed validated in CI before each publish; publish blocked on errors | ci-pipeline.yml.fixture |
| C2 | Old server kept warm for 30 days after go-live | Change ticket CHG-2231, approved 5 Nov 2026 |
| C3 | Automatic failover to a second FeedHarbour region | Planned; FeedHarbour says "on the roadmap" |
| C4 | Service account key rotated every 90 days | Not yet set up |
