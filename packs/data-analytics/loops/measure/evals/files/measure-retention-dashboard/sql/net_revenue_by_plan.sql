-- Net revenue per plan per week (Callum's definition: gross minus refunds, no test accounts)
-- author: finance-analytics
SELECT
    date_trunc('week', o.ordered_at)                         AS week_start,
    o.plan,
    SUM(o.order_total_pence) / 100.0                         AS gross_revenue_gbp,
    SUM(COALESCE(r.refund_pence, 0)) / 100.0                 AS refunds_gbp,
    (SUM(o.order_total_pence) - SUM(COALESCE(r.refund_pence, 0))) / 100.0 AS net_revenue_gbp,
    COUNT(DISTINCT oi.sku)                                   AS distinct_skus
FROM subs.orders o
JOIN subs.order_items oi ON oi.order_id = o.order_id
LEFT JOIN subs.refunds r ON r.order_id = o.order_id
WHERE o.subscriber_id NOT IN (SELECT subscriber_id FROM subs.test_accounts)
GROUP BY 1, 2
ORDER BY 1, 2;
