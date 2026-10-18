import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk import checkin  # noqa: E402
from fees import late_fee  # noqa: E402


class OnTimeReturns(unittest.TestCase):
    def test_returned_on_due_date_is_free(self):
        self.assertEqual(late_fee("book", date(2026, 3, 6), date(2026, 3, 6)), 0.0)

    def test_returned_early_is_free(self):
        self.assertEqual(late_fee("dvd", date(2026, 3, 6), date(2026, 3, 1)), 0.0)

    def test_checkin_on_time(self):
        item = {"barcode": "B100", "type": "book", "due": date(2026, 3, 6),
                "replacement_cost": 18.00, "card_type": "adult"}
        self.assertEqual(checkin(item, date(2026, 3, 6)), {"barcode": "B100", "fee": 0.0})


if __name__ == "__main__":
    unittest.main()
