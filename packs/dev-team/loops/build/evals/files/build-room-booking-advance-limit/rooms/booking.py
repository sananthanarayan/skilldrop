"""Meeting-room bookings for the Quillby Lane office."""
from dataclasses import dataclass
from datetime import datetime, timedelta


class BookingError(Exception):
    pass


@dataclass(frozen=True)
class Booking:
    room: str
    user: str
    start: datetime
    end: datetime


ROOMS = {"Larch": 12, "Birch": 10, "Hazel": 6, "Pod-1": 2, "Pod-2": 2}


class Diary:
    def __init__(self, clock=datetime.now):
        self._clock = clock
        self._bookings = []

    def book(self, room, user, start, end):
        self._validate(room, start, end)
        booking = Booking(room, user, start, end)
        self._check_clash([booking])
        self._bookings.append(booking)
        return booking

    def book_weekly(self, room, user, start, end, weeks):
        """Book the same slot every week for `weeks` weeks, all or nothing."""
        if weeks < 1:
            raise BookingError("weeks must be at least 1")
        self._validate(room, start, end)
        series = [
            Booking(room, user, start + timedelta(weeks=i), end + timedelta(weeks=i))
            for i in range(weeks)
        ]
        self._check_clash(series)
        self._bookings.extend(series)
        return series

    def cancel(self, booking):
        self._bookings.remove(booking)

    def for_room(self, room):
        return sorted((b for b in self._bookings if b.room == room), key=lambda b: b.start)

    def _validate(self, room, start, end):
        if room not in ROOMS:
            raise BookingError(f"unknown room {room!r}")
        if end <= start:
            raise BookingError("end must be after start")
        if start < self._clock():
            raise BookingError("cannot book in the past")

    def _check_clash(self, new):
        for b in new:
            for existing in self._bookings:
                if existing.room == b.room and existing.start < b.end and b.start < existing.end:
                    raise BookingError(f"{b.room} is already booked at {b.start:%Y-%m-%d %H:%M}")
