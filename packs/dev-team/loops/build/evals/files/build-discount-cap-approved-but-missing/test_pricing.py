import unittest

from pricing import apply_discount


class ApplyDiscountTest(unittest.TestCase):
    def test_ten_percent(self):
        self.assertEqual(apply_discount(1000, 10), 900)

    def test_negative_is_zero(self):
        self.assertEqual(apply_discount(1000, -5), 1000)

    def test_half_penny_rounds_up(self):
        # 12.5p off 250p at 5% -> 13p off
        self.assertEqual(apply_discount(250, 5), 237)

    def test_full_discount_clamped(self):
        self.assertEqual(apply_discount(1000, 120), 0)


if __name__ == "__main__":
    unittest.main()
