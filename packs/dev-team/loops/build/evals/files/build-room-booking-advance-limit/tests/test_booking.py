import unittest
from datetime import datetime, timedelta

from rooms.booking import BookingError, Diary

NOW = datetime(2026, 11, 9, 9, 0)


def diary():
    return Diary(clock=lambda: NOW)


def slot(days_ahead, hour=10, hours=1):
    start = NOW.replace(hour=hour) + timedelta(days=days_ahead)
    return start, start + timedelta(hours=hours)


class BookTests(unittest.TestCase):
    def test_books_a_free_room(self):
        d = diary()
        b = d.book("Hazel", "pat@quillby.example", *slot(2))
        self.assertEqual(d.for_room("Hazel"), [b])

    def test_rejects_a_clash(self):
        d = diary()
        d.book("Hazel", "pat@quillby.example", *slot(2))
        with self.assertRaises(BookingError):
            d.book("Hazel", "sam@quillby.example", *slot(2))

    def test_back_to_back_is_fine(self):
        d = diary()
        d.book("Hazel", "pat@quillby.example", *slot(2, hour=10))
        d.book("Hazel", "sam@quillby.example", *slot(2, hour=11))
        self.assertEqual(len(d.for_room("Hazel")), 2)

    def test_rejects_the_past(self):
        with self.assertRaises(BookingError):
            diary().book("Hazel", "pat@quillby.example", *slot(-1))

    def test_rejects_end_before_start(self):
        start, end = slot(2)
        with self.assertRaises(BookingError):
            diary().book("Hazel", "pat@quillby.example", end, start)

    def test_rejects_unknown_room(self):
        with self.assertRaises(BookingError):
            diary().book("Oak", "pat@quillby.example", *slot(2))


class WeeklyTests(unittest.TestCase):
    def test_books_every_week(self):
        d = diary()
        series = d.book_weekly("Larch", "pat@quillby.example", *slot(1), weeks=3)
        self.assertEqual([b.start - series[0].start for b in series],
                         [timedelta(weeks=0), timedelta(weeks=1), timedelta(weeks=2)])

    def test_a_clash_in_the_series_books_nothing(self):
        d = diary()
        d.book("Larch", "sam@quillby.example", *slot(15))
        with self.assertRaises(BookingError):
            d.book_weekly("Larch", "pat@quillby.example", *slot(1), weeks=3)
        self.assertEqual(len(d.for_room("Larch")), 1)

    def test_needs_at_least_one_week(self):
        with self.assertRaises(BookingError):
            diary().book_weekly("Larch", "pat@quillby.example", *slot(1), weeks=0)


if __name__ == "__main__":
    unittest.main()
