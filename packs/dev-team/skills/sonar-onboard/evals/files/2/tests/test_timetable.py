from datetime import datetime

from wayline.timetable import apply_delay, next_departures


def test_next_departures_orders_and_limits():
    now = datetime(2026, 10, 1, 8, 0)
    sched = [("12", datetime(2026, 10, 1, 8, 20)), ("7", datetime(2026, 10, 1, 8, 5)),
             ("3", datetime(2026, 10, 1, 7, 50))]
    assert next_departures(sched, now, limit=1) == [("7", datetime(2026, 10, 1, 8, 5))]


def test_apply_delay():
    assert apply_delay(("7", datetime(2026, 10, 1, 8, 5)), 4)[1] == datetime(2026, 10, 1, 8, 9)
