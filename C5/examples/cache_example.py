"""Demonstrates TTL memoization.

Run with:  python examples/cache_example.py
"""

import time

from handy import ttl_cache


@ttl_cache(seconds=2)
def expensive(x: int) -> int:
    print(f"  computing {x} ...")
    return x * x


print(expensive(4))  # computes
print(expensive(4))  # served from cache
time.sleep(2.1)
print(expensive(4))  # recomputed after expiry
