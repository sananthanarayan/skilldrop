from decimal import Decimal

LOYALTY_RATES = {"bronze": Decimal("0.00"), "silver": Decimal("0.03"), "gold": Decimal("0.05")}


def loyalty_discount(tier: str, subtotal: Decimal) -> Decimal:
    rate = LOYALTY_RATES.get(tier, Decimal("0.00"))
    return (subtotal * rate).quantize(Decimal("0.01"))
