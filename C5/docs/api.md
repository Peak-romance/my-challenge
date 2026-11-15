# API Reference

## `handy.config`

### `load_config(defaults=None, *, json_path=None, toml_path=None, env_prefix="", env_files=(".env",)) -> Config`

Build a `Config` by layering multiple sources. See
[docs/getting-started.md](getting-started.md) for the precedence order.

- **defaults** — baseline mapping (lowest precedence).
- **json_path / toml_path** — files overlaid on top of `defaults`.
- **env_prefix** — only env / `.env` keys starting with this prefix are
  injected; the remainder is lower-cased and `__` becomes a nested separator.
- **env_files** — `.env`-style files evaluated just below real env vars.

### `class Config`

- `get(key, default=None)` — value at dot-notation `key`, else `default`.
- `require(key)` — value at `key`, raises `KeyError` if absent.
- `as_dict()` — shallow copy of the underlying mapping.
- `key in config` — membership test.

## `handy.retry`

### `retry(on=Exception, *, attempts=3, backoff=0.1, max_backoff=30.0, jitter=True, on_retry=None)`

Decorator. Retries the wrapped callable with exponentially growing delay
(`backoff`, doubling, capped at `max_backoff`). When `jitter` is `True`, the
delay gets +/-25% noise. `on_retry(attempt, exception)` is called before each
wait. `backoff` may be `0` for instant retries.

## `handy.cache`

### `ttl_cache(seconds=60.0, maxsize=128)`

Decorator. Memoizes results for `seconds`, keeping at most `maxsize` entries
(oldest evicted first). Thread-safe. Wrapped function gains `cache_clear()`
and `cache_info()` helpers.

## `handy.rate`

### `class RateLimiter(calls, period)`

Token-bucket limiter allowing `calls` operations per `period` seconds.

- `try_acquire(tokens=1) -> bool` — take tokens immediately or return `False`.
- `acquire(tokens=1, *, timeout=None)` — block until available (or time out).
- `available() -> float` — current token count.
