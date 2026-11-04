import unittest
from decimal import Decimal

from cartcalc import LineItem, cart_total, subtotal, to_cents


def D(s):
    return Decimal(s)


class SubtotalTests(unittest.TestCase):
    def test_sums_lines(self):
        items = [LineItem("A", D("2.50"), 2), LineItem("B", D("10.00"), 1)]
        self.assertEqual(subtotal(items), D("15.00"))

    def test_empty_cart_is_zero(self):
        self.assertEqual(subtotal([]), D("0"))

    def test_negative_quantity_rejected(self):
        with self.assertRaises(ValueError):
            subtotal([LineItem("A", D("1.00"), -1)])

    def test_negative_price_rejected(self):
        with self.assertRaises(ValueError):
            subtotal([LineItem("A", D("-1.00"), 1)])


class CartTotalTests(unittest.TestCase):
    def test_no_tax(self):
        self.assertEqual(cart_total([LineItem("A", D("19.99"), 1)]), D("19.99"))

    def test_tax_rounded_once_half_up(self):
        # 3 x 0.335 = 1.005; with 10% tax = 1.1055 -> 1.11
        items = [LineItem("A", D("0.335"), 3)]
        self.assertEqual(cart_total(items, tax_rate=D("0.1")), D("1.11"))

    def test_negative_tax_rejected(self):
        with self.assertRaises(ValueError):
            cart_total([LineItem("A", D("1.00"), 1)], tax_rate=D("-0.1"))


class ToCentsTests(unittest.TestCase):
    def test_half_up(self):
        self.assertEqual(to_cents(D("2.345")), D("2.35"))
        self.assertEqual(to_cents(D("2.344")), D("2.34"))


if __name__ == "__main__":
    unittest.main()
