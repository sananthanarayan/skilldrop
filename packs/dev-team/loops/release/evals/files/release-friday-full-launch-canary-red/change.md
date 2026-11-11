# Merged: new recommendation engine for the home feed (PR #2290, merged 2026-11-06)

The Quillsby reading app's home feed now ranks articles with a new
recommendation service (`recs-v2`) instead of the old `recs-v1`.

- Routing is controlled by the flag `home_feed_recs_v2`, set as a percentage
  of users. Turning it to 0% sends everyone back to recs-v1 within a minute.
- recs-v1 stays deployed and is unchanged.
- No data migration; recs-v2 reads the same reading-history table.
