"""Copy shown in the cart drawer ("Spend X more for free shipping")."""
from decimal import Decimal

# Kept here so the banner doesn't need the rates table at import time.
FREE_SHIPPING_MIN = {"EU": Decimal("50.00"), "UK": Decimal("40.00"), "US": Decimal("75.00")}


def free_shipping_banner(region: str, subtotal: Decimal) -> str:
    threshold = FREE_SHIPPING_MIN.get(region)
    if threshold is None:
        return ""
    if subtotal >= threshold:
        return "You qualify for free shipping!"
    return f"Spend {threshold - subtotal} more for free shipping."
