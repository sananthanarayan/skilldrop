-- Active customers, October 2026 (Growth)
-- A customer is active if someone on the account logged in during the month.
-- Trials excluded.
SELECT COUNT(*) AS active_customers
FROM app.customers c
JOIN app.users u ON u.customer_id = c.customer_id
WHERE c.status <> 'trial'
  AND u.last_login_at >= '2026-10-01'
  AND u.last_login_at <  '2026-10-31';
