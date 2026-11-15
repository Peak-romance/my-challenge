"""A thread-safe token-bucket rate limiter."""

from __future__ import annotations

import threading
import time
from typing import Optional


class RateLimiter:
    """Allow at most ``calls`` operations every ``period`` seconds.

    The limiter starts full and refills continuously. It is safe to share a
    single instance across multiple threads.

    Parameters
    ----------
    calls:
        Number of tokens replenished per ``period`` (must be >= 1).
    period:
        Refill window in seconds (must be positive).
    """

    def __init__(self, calls: int, period: float) -> None:
        if calls < 1:
            raise ValueError("calls must be >= 1")
        if period <= 0:
            raise ValueError("period must be positive")
        self._calls = calls
        self._period = period
        self._tokens: float = float(calls)
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def try_acquire(self, tokens: int = 1) -> bool:
        """Take ``tokens`` immediately if available, else return ``False``."""
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def acquire(self, tokens: int = 1, *, timeout: Optional[float] = None) -> None:
        """Block until ``tokens`` are available (or ``timeout`` elapses)."""
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            if self.try_acquire(tokens):
                return
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError("RateLimiter.acquire timed out")
            time.sleep(min(0.01, self._period / self._calls))

    def available(self) -> float:
        """Return the current (refilled) token count."""
        with self._lock:
            self._refill()
            return self._tokens

    # -- internals ------------------------------------------------------- #
    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._updated
        if elapsed <= 0:
            return
        self._tokens = min(
            self._calls,
            self._tokens + elapsed * (self._calls / self._period),
        )
        self._updated = now
