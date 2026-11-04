-- Active customers, October 2026 (Finance)
-- A customer is active if they made a successful payment in the month.
SELECT COUNT(DISTINCT p.customer_id) AS active_customers
FROM app.payments p
WHERE p.status = 'succeeded'
  AND p.paid_at >= '2026-10-01'
  AND p.paid_at <  '2026-11-01';
