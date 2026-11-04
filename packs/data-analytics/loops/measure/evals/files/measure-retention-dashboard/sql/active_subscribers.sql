-- Active subscribers by plan at the end of each week
-- author: growth-analytics
SELECT
    date_trunc('week', d.day)  AS week_start,
    s.plan,
    COUNT(DISTINCT s.subscriber_id) AS active_subscribers
FROM generate_series(
        (now() - interval '12 weeks')::date,
        now()::date,
        interval '1 day'
     ) AS d(day)
JOIN subs.subscribers s
  ON s.created_at <= d.day
 AND (s.cancelled_at IS NULL OR s.cancelled_at > d.day)
WHERE extract(isodow FROM d.day) = 7   -- Sunday = end of week
GROUP BY 1, 2
ORDER BY 1, 2;
