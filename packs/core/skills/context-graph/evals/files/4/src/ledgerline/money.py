"""Money as integer minor units (ADR-0009)."""

MINOR_DIGITS = {"USD": 2, "EUR": 2, "JPY": 0}


def to_minor(amount_str: str, currency: str) -> int:
    digits = MINOR_DIGITS[currency]
    whole, _, frac = amount_str.partition(".")
    frac = (frac + "0" * digits)[:digits]
    return int(whole) * 10**digits + (int(frac) if digits else 0)
