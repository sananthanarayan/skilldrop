-- Share of sessions where a site ran out before closing, per site per month
-- Dialect: PostgreSQL 16
SELECT
  site_id,
  DATE_TRUNC('month', session_date) AS month,
  SUM(CASE WHEN ran_out_before_close THEN 1 ELSE 0 END) / COUNT(*) * 100 AS stockout_rate_pct
FROM sessions
GROUP BY site_id, DATE_TRUNC('month', session_date);
