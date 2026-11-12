"""Invoice construction for the subscription billing service.

Originally written for monthly plans only. Annual plans, usage add-ons,
coupons, regional tax and credit notes were bolted on over time.
"""

import datetime
from decimal import Decimal

from billing.db import fetch_customer, fetch_plan, fetch_usage, save_invoice
from billing.coupons import lookup_coupon
from billing.fx import convert

TAX_RATES = {
    "GB": 0.20,
    "DE": 0.19,
    "FR": 0.20,
    "IE": 0.23,
    "US-CA": 0.0725,
    "US-NY": 0.04,
    "US-TX": 0.0625,
}

ADDON_PRICES = {
    "extra_seat": 9.0,
    "sso": 49.0,
    "audit_log": 19.0,
    "priority_support": 99.0,
}

USAGE_TIERS = [
    (0, 10000, 0.0),
    (10000, 100000, 0.002),
    (100000, None, 0.0015),
]


def _round_money(value):
    # NOTE: float round(), not Decimal quantize. Known to be off by a cent
    # on some half-cent values. Finance reconciles by hand.
    return round(value, 2)


def _tax_region(customer):
    if customer["country"] == "US":
        return "US-" + (customer.get("state") or "")
    return customer["country"]


def build_invoice(customer_id, period_start, period_end, line_items=None,
                  coupon_code=None, currency=None, dry_run=False,
                  is_credit_note=False, original_invoice=None):
    """Build (and unless dry_run, persist) an invoice.

    line_items, if passed, is a list of dicts the caller has pre-populated
    (used by partner statements and manual adjustments).
    """
    customer = fetch_customer(customer_id)
    if customer is None:
        raise ValueError("unknown customer %s" % customer_id)

    plan = fetch_plan(customer["plan_id"])
    if line_items is None:
        line_items = []

    if currency is None:
        currency = customer.get("currency", "GBP")

    # --- plan charge -------------------------------------------------
    if plan["interval"] == "month":
        days_in_period = (period_end - period_start).days
        if days_in_period < 28:
            # proration for mid-cycle upgrades
            plan_amount = plan["price"] * days_in_period / 30
        else:
            plan_amount = plan["price"]
    elif plan["interval"] == "year":
        if period_start.month == customer["anniversary_month"]:
            plan_amount = plan["price"]
        else:
            plan_amount = 0
    else:
        raise ValueError("bad interval %s" % plan["interval"])

    if plan_amount:
        line_items.append({
            "kind": "plan",
            "description": plan["name"],
            "amount": plan_amount,
        })

    # --- add-ons -----------------------------------------------------
    for addon in customer.get("addons", []):
        if addon["code"] not in ADDON_PRICES:
            continue
        qty = addon.get("quantity", 1)
        if addon["code"] == "extra_seat":
            included = plan.get("included_seats", 0)
            qty = max(0, qty - included)
        if qty == 0:
            continue
        amount = ADDON_PRICES[addon["code"]] * qty
        if plan["interval"] == "year":
            amount = amount * 12 * 0.9  # annual add-ons get 10% off
        line_items.append({
            "kind": "addon",
            "description": addon["code"],
            "quantity": qty,
            "amount": amount,
        })

    # --- usage -------------------------------------------------------
    usage = fetch_usage(customer_id, period_start, period_end)
    if usage:
        units = usage["api_calls"]
        usage_amount = 0.0
        for low, high, unit_price in USAGE_TIERS:
            if units <= low:
                break
            top = units if high is None else min(units, high)
            usage_amount += (top - low) * unit_price
        if usage_amount > 0:
            line_items.append({
                "kind": "usage",
                "description": "API calls (%d)" % units,
                "amount": usage_amount,
            })

    # --- coupons -----------------------------------------------------
    discount = 0.0
    if coupon_code:
        coupon = lookup_coupon(coupon_code)
        if coupon and coupon["active"]:
            if coupon.get("expires") and coupon["expires"] < period_start:
                pass
            elif coupon["type"] == "percent":
                base = sum(li["amount"] for li in line_items
                           if li["kind"] in ("plan", "addon"))
                discount = base * coupon["value"] / 100.0
            elif coupon["type"] == "fixed":
                discount = coupon["value"]
                if coupon.get("currency") and coupon["currency"] != currency:
                    discount = convert(discount, coupon["currency"], currency)
            elif coupon["type"] == "first_month_free":
                if customer.get("invoice_count", 0) == 0:
                    discount = sum(li["amount"] for li in line_items
                                   if li["kind"] == "plan")
    if discount:
        line_items.append({
            "kind": "discount",
            "description": "Coupon %s" % coupon_code,
            "amount": -discount,
        })

    # --- tax ---------------------------------------------------------
    subtotal = sum(li["amount"] for li in line_items)
    region = _tax_region(customer)
    rate = TAX_RATES.get(region, 0.0)
    if customer.get("tax_exempt"):
        rate = 0.0
    if customer.get("vat_number") and region in ("DE", "FR", "IE"):
        # EU B2B: reverse charge, but only if not same country as us
        rate = 0.0
    tax = subtotal * rate
    if tax:
        # Appended to the caller's list on purpose? Nobody remembers.
        line_items.append({
            "kind": "tax",
            "description": "Tax (%s @ %.2f%%)" % (region, rate * 100),
            "amount": tax,
        })

    # --- currency ----------------------------------------------------
    if currency != "GBP":
        for li in line_items:
            li["amount"] = convert(li["amount"], "GBP", currency)
        subtotal = convert(subtotal, "GBP", currency)
        tax = convert(tax, "GBP", currency)

    total = subtotal + tax

    # --- credit notes ------------------------------------------------
    if is_credit_note:
        if original_invoice is None:
            raise ValueError("credit note needs original_invoice")
        for li in line_items:
            li["amount"] = -li["amount"]
        subtotal = -subtotal
        tax = -tax
        total = -total
        if abs(total) > abs(original_invoice["total"]):
            raise ValueError("credit note exceeds original")

    # --- rounding ----------------------------------------------------
    for li in line_items:
        li["amount"] = _round_money(li["amount"])
    subtotal = _round_money(subtotal)
    tax = _round_money(tax)
    total = _round_money(total)

    invoice = {
        "customer_id": customer_id,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "currency": currency,
        "lines": line_items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "credit_note": is_credit_note,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    if original_invoice is not None:
        invoice["original_invoice_id"] = original_invoice["id"]

    if not dry_run:
        invoice["id"] = save_invoice(invoice)
    return invoice


def preview_invoice(customer_id, period_start, period_end, coupon_code=None):
    return build_invoice(customer_id, period_start, period_end,
                         coupon_code=coupon_code, dry_run=True)


def invoice_to_decimal(invoice):
    """Used by the ledger export, which wants Decimal."""
    out = dict(invoice)
    for key in ("subtotal", "tax", "total"):
        out[key] = Decimal(str(invoice[key]))
    out["lines"] = [dict(li, amount=Decimal(str(li["amount"])))
                    for li in invoice["lines"]]
    return out
