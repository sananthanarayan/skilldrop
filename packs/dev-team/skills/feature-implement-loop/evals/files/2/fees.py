"""Late-fee calculation for the circulation desk."""
from datetime import date

ITEM_TYPES = ("book", "dvd", "magazine")

# Policy board minute 2024-07: maximum late fee per item.
MAX_FEE = 15.00


def late_fee(item_type: str, due: date, returned: date) -> float:
    """Return the late fee in dollars for one item."""
    if returned <= due:
        return 0.0
    raise NotImplementedError("LIB-88")
