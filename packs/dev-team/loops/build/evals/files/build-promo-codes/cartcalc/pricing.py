"""Cart totals.

Conventions in this module:
- All money is Decimal. Never float.
- Intermediate values are kept at full precision; round to cents once, at the end,
  half-up (finance signed this off in 2025, see docs/rounding.md in the main repo).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

CENT = Decimal("0.01")
ZERO = Decimal("0")


@dataclass(frozen=True)
class LineItem:
    sku: str
    unit_price: Decimal
    quantity: int


def to_cents(amount: Decimal) -> Decimal:
    """Round a money amount to cents, half-up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def subtotal(items: Iterable[LineItem]) -> Decimal:
    """Sum of unit_price * quantity, unrounded."""
    total = ZERO
    for item in items:
        if item.quantity < 0:
            raise ValueError(f"negative quantity for {item.sku}")
        if item.unit_price < ZERO:
            raise ValueError(f"negative price for {item.sku}")
        total += item.unit_price * item.quantity
    return total


def cart_total(items: Iterable[LineItem], tax_rate: Decimal = ZERO) -> Decimal:
    """Total to charge: subtotal plus tax, rounded to cents once."""
    if tax_rate < ZERO:
        raise ValueError("tax_rate must not be negative")
    sub = subtotal(items)
    return to_cents(sub + sub * tax_rate)
