"""Legacy quote service (Python 2-era code, ported to 3 in 2021). Being retired."""
import random
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

CATALOGUE = {
    "TEA-001": (450, "standard"),
    "MUG-002": (899, "standard"),
    "BOOK-05": (1299, "zero"),
    "CHILD-SEAT-01": (12500, "reduced"),
    "BOOSTER-02": (2250, "reduced"),
    "PRAM-03": (31090, "reduced"),
}
VAT = {"standard": Decimal("0.20"), "reduced": Decimal("0.05"), "zero": Decimal("0")}


def quote(request):
    items = request.get("items") or []
    if not items:
        return 422, {"error": "empty_basket"}
    qty_by_sku = {}
    for item in items:
        if item["sku"] not in CATALOGUE:
            return 422, {"error": "unknown_sku", "sku": item["sku"]}
        if item["qty"] < 1:
            return 422, {"error": "invalid_qty", "sku": item["sku"]}
        qty_by_sku[item["sku"]] = qty_by_sku.get(item["sku"], 0) + item["qty"]
    lines = []
    for sku in set(qty_by_sku):  # set: line order is whatever the hash gives
        price, band = CATALOGUE[sku]
        line_total = price * qty_by_sku[sku]
        vat = int((Decimal(line_total) * VAT[band]).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        lines.append({"sku": sku, "qty": qty_by_sku[sku], "unit_price_minor": price,
                      "line_total_minor": line_total, "vat_band": band, "vat_minor": vat})
    subtotal = sum(l["line_total_minor"] for l in lines)
    vat_total = sum(l["vat_minor"] for l in lines)
    return 200, {
        "quote_id": "Q-%08x" % random.getrandbits(32),
        "quoted_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "currency": request.get("currency", "GBP"),
        "lines": lines,
        "subtotal_minor": subtotal,
        "vat_minor": vat_total,
        "total_minor": subtotal + vat_total,
    }
