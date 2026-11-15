"""Resilient retries with exponential backoff and optional jitter.

The :func:`retry` decorator wraps a callable so that transient failures are
retried with a growing delay, which is the standard mitigation for flaky
network or downstream services.
"""

from __future__ import annotations

import functools
import random
import time
from typing import Callable, TypeVar, Union

T = TypeVar("T")
_ExceptionSpec = Union[type[BaseException], tuple[type[BaseException], ...]]


def retry(
    on: _ExceptionSpec = Exception,
    *,
    attempts: int = 3,
    backoff: float = 0.1,
    max_backoff: float = 30.0,
    jitter: bool = True,
    on_retry: Optional[Callable[[int, BaseException], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry ``func`` with exponential backoff when ``on`` is raised.

    Parameters
    ----------
    on:
        Exception type(s) that trigger a retry.
    attempts:
        Total tries including the first. Must be >= 1.
    backoff:
        Initial delay in seconds; doubles after each failed attempt.
    max_backoff:
        Upper bound applied to the computed delay.
    jitter:
        Add +/-25% random noise to the delay to avoid synchronized retries
        ("thundering herd").
    on_retry:
        Optional callback ``(attempt, exception)`` invoked before each wait.

    Example
    -------
    >>> @retry(on=ConnectionError, attempts=5, backoff=0.2)
    ... def call_api() -> str: ...
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    if backoff < 0:
        raise ValueError("backoff must be non-negative")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = backoff
            last_exc: Optional[BaseException] = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except on as exc:  # type: ignore[misc]
                    last_exc = exc
                    if attempt >= attempts:
                        break
                    wait = min(delay, max_backoff)
                    if jitter:
                        wait *= 0.75 + random.random() * 0.5
                    if on_retry is not None:
                        on_retry(attempt, exc)
                    time.sleep(wait)
                    delay *= 2
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator
