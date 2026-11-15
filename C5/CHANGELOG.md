# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-03

### Added
- `handy.config` — layered configuration loader with deep-merge and a
  documented precedence (`defaults < json < toml < .env < environment`),
  dot-notation access, prefix filtering, and type coercion for env values.
- `handy.retry` — `@retry` decorator with exponential backoff, optional
  jitter, and an `on_retry` callback.
- `handy.cache` — `@ttl_cache` thread-safe TTL memoization with LRU eviction.
- `handy.rate` — `RateLimiter` token-bucket limiter (`try_acquire` /
  blocking `acquire` / `available`).

### Notes
- Zero runtime dependencies; supports Python 3.9–3.13 (TOML requires 3.11+).
