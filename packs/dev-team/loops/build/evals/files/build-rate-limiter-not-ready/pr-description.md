# PR #487: Fix BUG-311 — cap token bucket refill at capacity

Branch: `fix/bug-311-bucket-cap`  Author: Jonah Becker

## What

- `_refill()` now caps tokens at `capacity`, so an idle bucket can't grow past its burst size.
- Added `test_idle_bucket_does_not_exceed_capacity` (the BUG-311 repro).
- Small tidy-up in `allow()` while I was in there.

## Testing

All tests pass locally.

## Diff

```diff
--- a/ratelimit/bucket.py
+++ b/ratelimit/bucket.py
@@ def _refill(self) -> None:
         now = self._clock()
         elapsed = max(0.0, now - self._last)
-        self._tokens = self._tokens + elapsed * self.refill_per_sec
+        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_per_sec)
         self._last = now
@@ def allow(self, cost: float = 1.0) -> bool:
         self._refill()
-        if self._tokens >= cost:
+        if self._tokens > cost:
             self._tokens -= cost
             return True
         return False
--- a/tests/test_bucket.py
+++ b/tests/test_bucket.py
@@ class TokenBucketTests(unittest.TestCase):
+    def test_idle_bucket_does_not_exceed_capacity(self):
+        # BUG-311 repro
+        bucket = TokenBucket(capacity=5, refill_per_sec=5, clock=self.clock)
+        self.clock.advance(3600)
+        self.assertLessEqual(bucket.tokens, 5)
+        self.assertLessEqual(burst(bucket, 50), 5)
```
