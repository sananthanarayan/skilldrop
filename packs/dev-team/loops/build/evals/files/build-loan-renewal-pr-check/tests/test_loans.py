import unittest
from datetime import date, timedelta

from library.loans import LOAN_DAYS, Desk, LoanError


class LendTests(unittest.TestCase):
    def test_lend_sets_due_date(self):
        desk = Desk()
        loan = desk.lend("B-1", "M-1", date(2026, 3, 2))
        self.assertEqual(loan.due, date(2026, 3, 2) + timedelta(days=LOAN_DAYS))

    def test_cannot_lend_twice(self):
        desk = Desk()
        desk.lend("B-1", "M-1", date(2026, 3, 2))
        with self.assertRaises(LoanError):
            desk.lend("B-1", "M-2", date(2026, 3, 3))

    def test_held_item_goes_to_first_in_queue(self):
        desk = Desk()
        desk.place_hold("B-1", "M-2")
        with self.assertRaises(LoanError):
            desk.lend("B-1", "M-1", date(2026, 3, 2))
        desk.lend("B-1", "M-2", date(2026, 3, 2))


class RenewTests(unittest.TestCase):
    def setUp(self):
        self.desk = Desk()
        self.loan = self.desk.lend("B-1", "M-1", date(2026, 3, 2))  # due 2026-03-23

    def test_renew_moves_due_date_from_current_due_date(self):
        self.desk.renew("B-1", "M-1")
        self.assertEqual(self.loan.due, date(2026, 4, 6))

    def test_can_renew_twice(self):
        self.desk.renew("B-1", "M-1")
        self.desk.renew("B-1", "M-1")
        self.assertEqual(self.loan.renewals, 2)
        self.assertEqual(self.loan.due, date(2026, 4, 20))

    def test_renewal_limit(self):
        self.loan.renewals = 3
        with self.assertRaises(LoanError):
            self.desk.renew("B-1", "M-1")

    def test_hold_by_someone_else_blocks_renewal(self):
        self.desk.place_hold("B-1", "M-2")
        with self.assertRaises(LoanError):
            self.desk.renew("B-1", "M-1")

    def test_own_hold_does_not_block(self):
        self.desk.place_hold("B-1", "M-1")
        self.desk.renew("B-1", "M-1")
        self.assertEqual(self.loan.renewals, 1)

    def test_only_borrower_can_renew(self):
        with self.assertRaises(LoanError):
            self.desk.renew("B-1", "M-2")


if __name__ == "__main__":
    unittest.main()
