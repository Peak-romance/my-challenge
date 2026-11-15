"""Time-to-live (TTL) memoization with a bounded LRU eviction policy."""

from __future__ import annotations

import functools
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Optional, Tuple, TypeVar

T = TypeVar("T")
_CacheKey = Tuple[Any, Any]


def ttl_cache(
    seconds: float = 60.0,
    maxsize: int = 128,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Cache a function's results for ``seconds``, keeping at most ``maxsize``.

    Entries are recomputed once they expire or are evicted (oldest first).
    The cache is safe to share across threads.

    Parameters
    ----------
    seconds:
        Time-to-live for each cached entry, in seconds (must be > 0).
    maxsize:
        Maximum number of live entries (must be >= 1).

    Example
    -------
    >>> @ttl_cache(seconds=30)
    ... def get_quote(symbol: str) -> float: ...
    """
    if seconds <= 0:
        raise ValueError("seconds must be positive")
    if maxsize < 1:
        raise ValueError("maxsize must be >= 1")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        store: "OrderedDict[_CacheKey, Tuple[float, T]]" = OrderedDict()
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            key: _CacheKey = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            with lock:
                if key in store:
                    expires, value = store[key]
                    if now < expires:
                        store.move_to_end(key)
                        return value
                    del store[key]
                if len(store) >= maxsize:
                    store.popitem(last=False)
            value = func(*args, **kwargs)
            with lock:
                store[key] = (now + seconds, value)
            return value

        def cache_clear() -> None:
            with lock:
                store.clear()

        def cache_info() -> Tuple[int, int, float]:
            return (len(store), maxsize, seconds)

        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        wrapper.cache_info = cache_info  # type: ignore[attr-defined]
        return wrapper

    return decorator
