# Design note: Tax engine v2 for invoice generation

Owner: Priya Okonkwo (Billing platform)

## Why
The current invoice tax calculation is hand-rolled and gets Canadian HST/PST
combinations and US marketplace-facilitator states wrong in edge cases. v2 calls
Taxwell (external tax API) per invoice line and stores the result.

## Change
- `InvoiceBuilder` gets a `tax_engine` switch read from flag `billing.tax_engine_v2`
  (flag can target by tenant_id; it cannot target by %, but we could hash tenant_id).
- v2 writes line items to the new `invoice_line_tax_v2` table (jurisdiction breakdown
  per line). v1 code does not read this table. The invoice PDF renderer reads
  whichever table the invoice was built with.
- Finished invoices are rendered to PDF and emailed to the tenant's billing contacts
  by the existing nightly job, and synced to the tenant's accounting system
  (QuickBooks / Xero connectors) if they have one connected.

## Volume
- ~340 paying tenants. Most invoices are generated on the 1st of the month
  (about 6,500 invoices that day); the rest of the month is usage-based and
  mid-cycle upgrades, roughly 40-60 invoices/day.
- Current invoice generation failure rate (job errors needing manual re-run): ~0.6%.
