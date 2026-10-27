from decimal import Decimal, InvalidOperation

from ledgerline.errors import ParseError


def parse_amount(text: str) -> Decimal:
    """Parse '1,234.50' or '(12.00)' into a Decimal. Parentheses mean a debit."""
    cleaned = text.strip().replace(",", "")
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    try:
        value = Decimal(cleaned.strip("()"))
    except InvalidOperation:
        raise ParseError(f"amount {text!r} is not a number")
    return -value if negative else value
