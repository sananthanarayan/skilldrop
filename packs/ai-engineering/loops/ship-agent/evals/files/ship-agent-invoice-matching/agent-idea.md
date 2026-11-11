# Invoice matching agent: idea

**Team:** Accounts Payable, Larkspur Supplies (fictional)
**Launch owner:** Dana Whitlow, AP lead. She signs the pilot launch.

## What it does

Suppliers email PDF invoices to invoices@ap.larkspur.example. Anyone can email that address.

For each new message the agent:

1. Reads the email and its PDF attachment from the AP mailbox (read-only).
2. Pulls out the invoice number, supplier name, PO number and line totals.
3. Looks up the purchase order and the goods-received record in the ERP.
4. Writes a draft note into the finance queue saying one of three things:
   - **MATCH**: invoice lines agree with the PO and goods received
   - **MISMATCH**: says which lines differ and by how much
   - **NEEDS A PERSON**: anything it can't decide

A clerk reads every note and approves payment in the ERP themselves. The agent never approves payment and never changes anything in the ERP.

## Tools we want it to have

- AP mailbox: list messages, read a message, read an attachment. No sending.
- ERP: read a purchase order, read a goods-received record. Read-only.
- Finance queue: create a draft note.

No web access, no email sending, no shell. The finance queue shows notes as plain text (no links or images are rendered).

## Data

- The ERP holds supplier bank details and our negotiated PO prices. Both are confidential.
- The ERP MCP server also exposes a supplier bank details lookup. The agent does not need it.

## Numbers

- About 1,500 invoices a month. Month-end day peaks at about 120.
- Model spend must stay under $450 a month, all in.
- A clerk spends about 6 minutes per invoice today.

## What good looks like

We have 400 invoices from Q3 with the clerk's recorded decision (match / mismatch / needs a person).

- The agent's decision should agree with the clerk's on at least 95% of invoices.
- It must say MATCH where the clerk said MISMATCH no more than 1 time in 200.

## Launch plan

Two-week pilot on one supplier group (stationery and office supplies), then review.

The configuration we'd run it with is in `dot.claude/settings.json` and `dot.mcp.json`. They're stored without the leading dot.
