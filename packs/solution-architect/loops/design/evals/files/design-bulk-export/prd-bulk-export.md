# PRD: Bulk invoice export (CSV)

- **Product:** Ledgerline
- **Author:** Ines Moreau (PM, Billing)
- **Status:** Ratified — product review, 28 Oct 2026 (approvers: Ines Moreau, Kwame Asante (Eng Manager, Billing), Lotte Jansen (Head of Finance Ops))
- **Tracking:** LDG-2210

## Problem

Finance admins at our larger tenants reconcile invoices in their own accounting tools at month end. Today the only way to get invoice data out of Ledgerline is the invoice list page, which pages 100 rows at a time, or a support ticket asking us to run a query. In September 2026 support handled 61 export requests from 23 tenants; median time to fulfil was 2.5 working days. Finance admins at three tenants told us in calls that month-end close slips because they wait on us.

## Goals

| Goal | Success line |
|---|---|
| G1. A finance admin can get all of their tenant's invoices for a date range without contacting support | Export-related support tickets fall from 61/month to under 10/month within two months of launch |
| G2. Exports are fast enough to use during month-end close | 95% of exports are ready to download within 15 minutes of the request |

## Users

- **Finance Admin** role only. Other roles (Member, Viewer, Billing Contact) must not see or use the feature.

## Requirements

| ID | Priority | Requirement |
|---|---|---|
| R1 | Must | A Finance Admin can request a CSV export of invoices filtered by issue-date range (max 24 months) and status (any combination of draft, open, paid, void). |
| R2 | Must | One export can contain up to 2,000,000 rows. Our largest tenant today has 1.6M invoices. |
| R3 | Must | The requester is notified in-app and by email when the export is ready, with a download link. |
| R4 | Must | The download link works for 24 hours and only for the user who requested it. |
| R5 | Must | Export files are deleted 7 days after creation. |
| R6 | Must | Columns: invoice number, issue date, due date, status, customer name, customer email, currency, net, tax, gross, paid date. |
| R7 | Must | Every export request and every download is written to the tenant's audit log (who, when, filters, row count). |
| R8 | Should | A Finance Admin can see their last 10 exports and their status (queued, running, ready, failed, expired). |
| R9 | Could | Cancel a queued or running export. |

## Data

Export files contain customer names and email addresses (personal data) and invoice amounts. Same classification as the invoice table: Confidential.

## Non-goals

- Scheduled or recurring exports.
- Formats other than CSV (no XLSX, no PDF bundle).
- An export API for integrations. Covered separately in LDG-2302.
- Exporting line items. Invoice headers only.

## Open questions

None outstanding. (Line-item export was moved to non-goals at review.)
