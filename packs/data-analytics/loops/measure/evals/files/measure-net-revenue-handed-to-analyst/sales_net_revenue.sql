-- Sales team's "net revenue" by month and channel
-- Dialect: PostgreSQL 16
SELECT
  DATE_TRUNC('month', o.ordered_at) AS month,
  o.channel,
  SUM(o.order_total) AS net_revenue
FROM orders o
JOIN order_lines ol ON ol.order_id = o.order_id
WHERE o.status <> 'cancelled'
GROUP BY 1, 2;
