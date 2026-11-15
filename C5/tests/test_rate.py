"""Tests for handy.rate — token-bucket rate limiter."""

import time
import unittest

from handy import RateLimiter


class TestRateLimiter(unittest.TestCase):
    def test_try_acquire(self):
        rl = RateLimiter(calls=2, period=1.0)
        self.assertTrue(rl.try_acquire())
        self.assertTrue(rl.try_acquire())
        self.assertFalse(rl.try_acquire())
        self.assertAlmostEqual(rl.available(), 0.0, places=3)

    def test_refill(self):
        rl = RateLimiter(calls=1, period=0.05)
        self.assertTrue(rl.try_acquire())
        self.assertFalse(rl.try_acquire())
        time.sleep(0.1)
        self.assertTrue(rl.try_acquire())

    def test_acquire_blocks(self):
        rl = RateLimiter(calls=1, period=0.05)
        rl.acquire()
        start = time.monotonic()
        rl.acquire(timeout=1.0)
        self.assertLess(time.monotonic() - start, 1.0)


if __name__ == "__main__":
    unittest.main()
