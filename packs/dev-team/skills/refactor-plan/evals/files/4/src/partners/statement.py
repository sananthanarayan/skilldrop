"""Monthly partner (reseller) statements.

Resellers get a statement per sub-account showing what was billed and
how much tax was charged, so they can reclaim it.
"""

from billing.invoice import build_invoice
from partners.db import sub_accounts_for, save_statement


def partner_statement(partner_id, period_start, period_end):
    rows = []
    for account in sub_accounts_for(partner_id):
        lines = [{
            "kind": "partner_margin",
            "description": "Reseller margin",
            "amount": -account["margin"],
        }]
        build_invoice(account["customer_id"], period_start, period_end,
                      line_items=lines, dry_run=True)
        # build_invoice appends the tax line onto `lines`; we read it back
        # from our own list rather than from the returned invoice.
        tax_line = next((li for li in lines if li["kind"] == "tax"), None)
        rows.append({
            "customer_id": account["customer_id"],
            "net": sum(li["amount"] for li in lines if li["kind"] != "tax"),
            "tax": tax_line["amount"] if tax_line else 0.0,
        })
    return save_statement(partner_id, period_start, period_end, rows)
