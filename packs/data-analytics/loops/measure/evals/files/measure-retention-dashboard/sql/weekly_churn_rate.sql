-- Weekly churn rate by plan = cancellations in week / active at start of week
-- author: retention-team
WITH weeks AS (
    SELECT generate_series(
        date_trunc('week', now()) - interval '12 weeks',
        date_trunc('week', now()),
        interval '1 week'
    ) AS week_start
),
active_at_start AS (
    SELECT w.week_start, s.plan, COUNT(*) AS active_start
    FROM weeks w
    JOIN subs.subscribers s
      ON s.created_at < w.week_start
     AND (s.cancelled_at IS NULL OR s.cancelled_at >= w.week_start)
    GROUP BY 1, 2
),
cancels AS (
    SELECT date_trunc('week', s.cancelled_at) AS week_start, s.plan, COUNT(*) AS cancelled
    FROM subs.subscribers s
    WHERE s.cancelled_at IS NOT NULL
    GROUP BY 1, 2
)
SELECT
    a.week_start,
    a.plan,
    a.active_start,
    COALESCE(c.cancelled, 0)                        AS cancelled,
    COALESCE(c.cancelled, 0) / a.active_start * 100 AS churn_rate_pct
FROM active_at_start a
LEFT JOIN cancels c
  ON c.week_start = a.week_start
 AND c.plan = a.plan
ORDER BY 1, 2;
