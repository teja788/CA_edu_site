"""Thread-safe token-bucket rate limiter.

Used to respect Kite Connect's historical-data API limit (3 requests/second).
Clock and sleep are injectable so tests can exercise timing behaviour with a
fake clock and finish instantly (no real sleeping).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from tradingos.core.logging import get_logger

logger = get_logger(__name__)

# Refilling exactly `wait * rate` tokens can land one float ULP short of the
# requested n (e.g. 0.3333... * 3 == 0.9999999999999998), which would make
# acquire() loop on an unrepresentably small wait. Treat within-EPS as enough;
# at 3 tokens/second this equals ~0.3ns of accrual.
_EPS = 1e-9


class TokenBucket:
    """Classic token-bucket limiter.

    Tokens accrue continuously at `rate` tokens/second up to `capacity` (the
    burst size). `acquire(n)` blocks the caller (by calling the injected
    `sleep`) until `n` tokens are available, then debits them.
    """

    def __init__(
        self,
        rate: float,
        capacity: int,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if rate <= 0:
            raise ValueError("rate must be > 0")
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.rate = rate
        self.capacity = capacity
        self._clock = clock
        self._sleep = sleep
        self._tokens = float(capacity)
        self._last = clock()
        self._lock = threading.Lock()

    def _refill_locked(self) -> None:
        """Top up tokens based on elapsed time. Caller must hold `_lock`."""
        now = self._clock()
        elapsed = now - self._last
        self._last = now
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)

    def acquire(self, n: int = 1) -> None:
        """Block until `n` tokens are available, then consume them."""
        if n < 1:
            raise ValueError("n must be >= 1")
        if n > self.capacity:
            raise ValueError(f"cannot acquire {n} tokens; bucket capacity is {self.capacity}")
        while True:
            with self._lock:
                self._refill_locked()
                if self._tokens + _EPS >= n:
                    self._tokens = max(0.0, self._tokens - n)
                    return
                deficit = n - self._tokens
                wait = deficit / self.rate
            # Sleep outside the lock so other threads can still refill/acquire.
            logger.debug("rate limit: waiting %.4fs for %d token(s)", wait, n)
            self._sleep(wait)
