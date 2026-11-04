import unittest

from ratelimit import TokenBucket


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def burst(bucket: TokenBucket, n: int) -> int:
    return sum(1 for _ in range(n) if bucket.allow())


class TokenBucketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()

    def test_burst_allows_exactly_capacity(self):
        bucket = TokenBucket(capacity=5, refill_per_sec=5, clock=self.clock)
        self.assertEqual(burst(bucket, 10), 5)

    def test_refills_over_time(self):
        bucket = TokenBucket(capacity=5, refill_per_sec=5, clock=self.clock)
        burst(bucket, 10)
        self.clock.advance(0.5)
        self.assertGreaterEqual(bucket.tokens, 2.5)

    def test_idle_bucket_does_not_exceed_capacity(self):
        # BUG-311 repro
        bucket = TokenBucket(capacity=5, refill_per_sec=5, clock=self.clock)
        self.clock.advance(3600)
        self.assertLessEqual(bucket.tokens, 5)
        self.assertLessEqual(burst(bucket, 50), 5)

    def test_clock_going_backwards_does_not_add_tokens(self):
        bucket = TokenBucket(capacity=5, refill_per_sec=5, clock=self.clock)
        burst(bucket, 5)
        self.clock.advance(-10)
        self.assertFalse(bucket.allow())

    def test_cost_larger_than_capacity_is_refused(self):
        bucket = TokenBucket(capacity=5, refill_per_sec=5, clock=self.clock)
        self.assertFalse(bucket.allow(cost=6))

    def test_rejects_bad_arguments(self):
        with self.assertRaises(ValueError):
            TokenBucket(capacity=0, refill_per_sec=1, clock=self.clock)
        with self.assertRaises(ValueError):
            TokenBucket(capacity=1, refill_per_sec=-1, clock=self.clock)
        bucket = TokenBucket(capacity=1, refill_per_sec=1, clock=self.clock)
        with self.assertRaises(ValueError):
            bucket.allow(cost=0)


if __name__ == "__main__":
    unittest.main()
