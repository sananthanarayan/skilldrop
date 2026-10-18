-- monthly_donor_revenue.sql
-- Monthly donation revenue by region for the fundraising dashboard (PostgreSQL 16)

SELECT DISTINCT
    DATE_TRUNC('month', d.donated_at)                        AS month,
    a.region,
    SUM(d.amount_pence) / 100                                AS revenue_gbp,
    COUNT(d.donation_id)                                     AS gifts,
    SUM(d.amount_pence) / COUNT(DISTINCT d.donor_id) / 100   AS avg_per_donor_gbp
FROM donations d
JOIN donor_addresses a
    ON a.donor_id = d.donor_id
WHERE d.donated_at >= '2026-01-01'
  AND d.gift_aid_status <> 'rejected'
GROUP BY 1, 2
ORDER BY 1, 2;
