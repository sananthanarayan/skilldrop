from datetime import datetime, timedelta


def next_departures(schedule, now: datetime, limit: int = 5):
    """Return the next `limit` departures at or after `now` from a list of (route, datetime)."""
    upcoming = sorted((d for d in schedule if d[1] >= now), key=lambda d: d[1])
    return upcoming[:limit]


def apply_delay(departure, minutes: int):
    route, when = departure
    return route, when + timedelta(minutes=minutes)
