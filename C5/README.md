# handy

> Everyday Python utilities for working engineers — **zero runtime dependencies**.

[![CI](https://github.com/Peak-romance/handy/actions/workflows/ci.yml/badge.svg)](https://github.com/Peak-romance/handy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/Peak-romance/handy)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](pyproject.toml)

`handy` is a small, boring-on-purpose standard-library toolkit that covers the
four things almost every Python service eventually needs:

| Module | What it gives you |
| ------ | ---------------- |
| `handy.config` | Layered configuration (defaults / JSON / TOML / `.env` / env) with deep-merge and dot access |
| `handy.retry`  | `@retry` decorator with exponential backoff + jitter |
| `handy.cache`  | `@ttl_cache` thread-safe TTL memoization with LRU eviction |
| `handy.rate`   | `RateLimiter` token-bucket limiter |

No third-party runtime dependencies. Works on Python 3.9–3.13 (TOML needs 3.11+).

---

## Installation

```bash
pip install handy-py
```

Or install from a checkout for development:

```bash
git clone https://github.com/Peak-romance/handy.git
cd handy
python -m pip install -e .
```

## Quick start

### Layered configuration

```python
from handy import load_config

cfg = load_config(
    defaults={"debug": False, "db": {"host": "localhost", "port": 5432}},
    env_prefix="APP_",
)
cfg.get("db.host")   # "localhost"
cfg.get("debug")     # False  — override with APP_DEBUG=true
```

Precedence (lowest → highest):
`defaults < json < toml < .env < environment variables`.

### Retry a flaky call

```python
from handy import retry

@retry(on=ConnectionError, attempts=5, backoff=0.2, jitter=True)
def call_api():
    ...
```

### Cache an expensive result

```python
from handy import ttl_cache

@ttl_cache(seconds=30)
def get_quote(symbol: str):
    ...
```

### Throttle requests

```python
from handy import RateLimiter

limiter = RateLimiter(calls=10, period=1.0)
if limiter.try_acquire():
    send_request()
```

Runnable examples live in [`examples/`](examples). Full reference in
[`docs/api.md`](docs/api.md) and [`docs/getting-started.md`](docs/getting-started.md).

## Development

```bash
make install     # pip install -e .
make test        # python -m unittest discover -s tests -v
make lint        # byte-compile smoke test
```

The test suite uses only the standard library (`unittest`); **pytest is not
required** to validate or use the package.

## Project layout

```
handy/
├── .github/              # issue/PR templates, CODEOWNERS, CI workflow
├── docs/                 # getting-started + API reference
├── examples/             # runnable snippets
├── src/handy/            # the package (config, retry, cache, rate)
├── tests/                # stdlib unittest suite (16 tests)
├── LICENSE               # MIT
├── CODE_OF_CONDUCT.md    # Contributor Covenant 2.1
├── CONTRIBUTING.md       # contributor guide
├── SECURITY.md           # vulnerability reporting
├── CHANGELOG.md          # Keep a Changelog
├── pyproject.toml        # PEP 621 metadata, src-layout
├── Makefile
└── README.md
```

## About this repository (challenge context)

This repository was produced as the deliverable for the **C5 GitHub Repository
Challenge**. Two companion documents are included for transparency and grading:

- [`AI_USAGE_LOG.md`](AI_USAGE_LOG.md) — how AI tooling was used to build this
  repo (traceability for the *AI usage* criterion).
- [`DELIVERABLE_GUIDE.md`](DELIVERABLE_GUIDE.md) — the "拿来说明" walkthrough,
  including a criterion-by-criterion mapping and an AAR (After-Action Review)
  for the *reflection* criterion.

## License

[MIT](LICENSE) © 2026 Peak-romance.
