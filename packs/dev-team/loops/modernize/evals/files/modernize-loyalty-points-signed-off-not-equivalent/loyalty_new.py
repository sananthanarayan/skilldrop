"""Loyalty points, rewritten for the new points service."""
from datetime import date

CAP_PER_BASKET = 500
PENCE_PER_POINT = 500
DOUBLE_POINTS_WEEKDAY = 1  # Tuesday


def points(spend_pence: int, date_str: str) -> int:
    day = date.fromisoformat(date_str)
    pts = min(round(spend_pence / PENCE_PER_POINT), CAP_PER_BASKET)
    if day.weekday() == DOUBLE_POINTS_WEEKDAY:
        pts *= 2
    return pts
