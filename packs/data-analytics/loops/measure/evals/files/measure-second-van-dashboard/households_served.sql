-- Households served per district per month (feeds "Demand by district")
-- Dialect: PostgreSQL 16
SELECT
  s.district,
  DATE_TRUNC('month', v.visit_at) AS month,
  COUNT(v.household_id) AS households_served
FROM visits v
JOIN parcel_items pi ON pi.visit_id = v.visit_id
JOIN sites s ON s.site_id = v.site_id
WHERE v.visit_at >= DATE '2026-01-01'
GROUP BY s.district, DATE_TRUNC('month', v.visit_at)
ORDER BY month, s.district;
