"""handy — Everyday Python utilities for working engineers.

A small, dependency-free toolkit covering the boring-but-necessary bits of
building production Python services: layered configuration, resilient retries,
in-memory TTL caching, and rate limiting.

Example
-------
>>> from handy import config, retry, ttl_cache, RateLimiter
"""

from .config import Config, load_config
from .retry import retry
from .cache import ttl_cache
from .rate import RateLimiter

__version__ = "0.1.0"

__all__ = ["Config", "load_config", "retry", "ttl_cache", "RateLimiter"]
