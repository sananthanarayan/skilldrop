from decimal import Decimal

from shipcalc.discounts import loyalty_discount


def test_gold_gets_five_percent():
    assert loyalty_discount("gold", Decimal("100.00")) == Decimal("5.00")


def test_unknown_tier_gets_nothing():
    assert loyalty_discount("platinum", Decimal("100.00")) == Decimal("0.00")
