"""Finance's monthly revenue report. Run by cron on the 2nd of each month.

Recomputes tax per invoice so the report can split revenue by region.
"""

import csv
import sys

from billing.db import invoices_between, fetch_customer

# copied from billing/invoice.py so the report doesn't need the whole
# billing import chain (2023)
TAX_RATES = {
    "GB": 0.20,
    "DE": 0.19,
    "FR": 0.20,
    "IE": 0.23,
    "US-CA": 0.0725,
    "US-NY": 0.04,
}


def tax_for(customer, subtotal):
    if customer["country"] == "US":
        region = "US-" + (customer.get("state") or "")
    else:
        region = customer["country"]
    rate = TAX_RATES.get(region, 0.0)
    if customer.get("tax_exempt"):
        rate = 0.0
    return region, round(subtotal * rate, 2)


def main(start, end, out=sys.stdout):
    writer = csv.writer(out)
    writer.writerow(["invoice_id", "region", "subtotal", "tax"])
    for inv in invoices_between(start, end):
        customer = fetch_customer(inv["customer_id"])
        region, tax = tax_for(customer, inv["subtotal"])
        writer.writerow([inv["id"], region, inv["subtotal"], tax])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
