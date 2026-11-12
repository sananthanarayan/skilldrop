"""Shipping cost for a cart. Rates come from the generated table."""
import os
from decimal import Decimal, ROUND_HALF_UP

from shipcalc.generated.rates_table import RATES


def _free_shipping_enabled() -> bool:
    # Rolled out per environment; off unless explicitly turned on.
    return os.environ.get("SHIPCALC_FF_FREE_SHIPPING", "off") == "on"


def shipping_cost(region: str, subtotal: Decimal, weight_kg: Decimal) -> Decimal:
    rate = RATES[region]
    if _free_shipping_enabled() and subtotal >= Decimal(str(rate["free_threshold"])):
        return Decimal("0.00")
    cost = Decimal(str(rate["base_rate"])) + Decimal(str(rate["per_kg"])) * weight_kg
    return cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
