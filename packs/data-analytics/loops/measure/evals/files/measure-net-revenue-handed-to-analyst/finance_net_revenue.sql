-- Finance's "net revenue" by month and channel
-- Dialect: PostgreSQL 16
WITH dispatched AS (
  SELECT DATE_TRUNC('month', ol.dispatched_at) AS month, o.channel, SUM(ol.line_net) AS gross_net
  FROM order_lines ol
  JOIN orders o ON o.order_id = ol.order_id
  WHERE ol.dispatched_at IS NOT NULL
  GROUP BY 1, 2
),
refunded AS (
  SELECT DATE_TRUNC('month', r.refunded_at) AS month, o.channel, SUM(r.amount_net) AS refunds_net
  FROM refunds r
  JOIN orders o ON o.order_id = r.order_id
  WHERE r.reason <> 'test'
  GROUP BY 1, 2
)
SELECT d.month, d.channel, d.gross_net - COALESCE(rf.refunds_net, 0) AS net_revenue
FROM dispatched d
LEFT JOIN refunded rf ON rf.month = d.month AND rf.channel = d.channel;
