"""Token bucket rate limiter.

A bucket holds up to `capacity` tokens and gains `refill_per_sec` tokens per second.
Each request spends `cost` tokens; a request is allowed when enough tokens are left.
The clock is injectable so tests do not sleep.
"""
from __future__ import annotations

import time
from typing import Callable


class TokenBucket:
    def __init__(
        self,
        capacity: float,
        refill_per_sec: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_per_sec < 0:
            raise ValueError("refill_per_sec must not be negative")
        self.capacity = float(capacity)
        self.refill_per_sec = float(refill_per_sec)
        self._clock = clock
        self._tokens = float(capacity)
        self._last = clock()

    def _refill(self) -> None:
        now = self._clock()
        elapsed = max(0.0, now - self._last)
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_per_sec)
        self._last = now

    @property
    def tokens(self) -> float:
        self._refill()
        return self._tokens

    def allow(self, cost: float = 1.0) -> bool:
        """Spend `cost` tokens if available. Returns True if the request is allowed."""
        if cost <= 0:
            raise ValueError("cost must be positive")
        self._refill()
        if self._tokens > cost:
            self._tokens -= cost
            return True
        return False
