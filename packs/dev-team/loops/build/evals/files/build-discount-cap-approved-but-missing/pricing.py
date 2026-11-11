"""Till pricing helpers."""
import math


def apply_discount(total_pence, percent):
    """Return total_pence after a percentage discount, in whole pence."""
    if percent < 0:
        percent = 0
    if percent > 100:
        percent = 100
    discount = math.floor(total_pence * percent / 100 + 0.5)
    return total_pence - discount
