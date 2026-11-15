"""Demonstrates retrying a flaky operation.

Run with:  python examples/retry_example.py
"""

import random

from handy import retry


@retry(on=ConnectionError, attempts=5, backoff=0.2, jitter=True)
def unstable_request() -> str:
    if random.random() < 0.7:
        raise ConnectionError("transient network error")
    return "success"


print("result:", unstable_request())
