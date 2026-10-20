"""Quote service rewrite. Same contract as pricing_v1, catalogue now loaded from config."""
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

CATALOGUE = {
    "TEA-001": (450, "standard"),
    "MUG-002": (899, "standard"),
    "BOOK-05": (1299, "zero"),
    "CHILD-SEAT-01": (12500, "reduced"),
    "BOOSTER-02": (2250, "reduced"),
    "PRAM-03": (31090, "reduced"),
}
VAT = {"standard": Decimal("0.20"), "reduced": Decimal("0.05"), "zero": Decimal("0")}


class QuoteError(Exception):
    def __init__(self, code, sku=None):
        super().__init__(code)
        self.body = {"error": code} if sku is None else {"error": code, "sku": sku}


@dataclass
class Line:
    sku: str
    qty: int

    def to_dict(self):
        price, band = CATALOGUE[self.sku]
        line_total = price * self.qty
        vat = round(Decimal(line_total) * VAT[band])
        return {"sku": self.sku, "qty": self.qty, "unit_price_minor": price,
                "line_total_minor": line_total, "vat_band": band, "vat_minor": int(vat)}


def _lines(items):
    if not items:
        raise QuoteError("empty_basket")
    merged = {}
    for item in items:
        if item["sku"] not in CATALOGUE:
            raise QuoteError("unknown_sku", item["sku"])
        if item["qty"] < 1:
            raise QuoteError("invalid_qty", item["sku"])
        merged[item["sku"]] = merged.get(item["sku"], 0) + item["qty"]
    return [Line(sku, qty).to_dict() for sku, qty in sorted(merged.items())]


def quote(request):
    try:
        lines = _lines(request.get("items") or [])
    except QuoteError as err:
        return 422, err.body
    subtotal = sum(l["line_total_minor"] for l in lines)
    vat_total = sum(l["vat_minor"] for l in lines)
    return 200, {
        "quote_id": "Q-" + secrets.token_hex(4),
        "quoted_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "currency": request.get("currency", "GBP"),
        "lines": lines,
        "subtotal_minor": subtotal,
        "vat_minor": vat_total,
        "total_minor": subtotal + vat_total,
    }
