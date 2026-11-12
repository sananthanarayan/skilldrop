"""Check-in handler used by the desk app."""
from datetime import date

from fees import late_fee


def checkin(item: dict, returned: date | None = None) -> dict:
    """item has keys: barcode, type, due, replacement_cost, card_type."""
    returned = returned or date.today()
    fee = late_fee(item["type"], item["due"], returned)
    return {"barcode": item["barcode"], "fee": fee}
