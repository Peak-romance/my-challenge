"""Demonstrates rate limiting.

Run with:  python examples/rate_example.py
"""

from handy import RateLimiter

limiter = RateLimiter(calls=3, period=1.0)
for i in range(5):
    if limiter.try_acquire():
        print(f"request {i}: allowed")
    else:
        print(f"request {i}: throttled")
