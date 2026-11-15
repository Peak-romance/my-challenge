# Getting Started

`handy` is a tiny, dependency-free Python toolkit for the boring-but-necessary
parts of production code: configuration, retries, caching, and rate limiting.

## Installation

```bash
pip install handy-py
```

Or, for local development, install from a checkout:

```bash
git clone https://github.com/Peak-romance/handy.git
cd handy
python -m pip install -e .
```

> Requires Python 3.9+. TOML configuration support needs Python 3.11+.

## Your first 60 seconds

### 1. Layered configuration

```python
from handy import load_config

cfg = load_config(
    defaults={"debug": False, "db": {"host": "localhost", "port": 5432}},
    env_prefix="APP_",
)
print(cfg.get("db.host"))   # localhost
print(cfg.get("debug"))     # False (overridable via APP_DEBUG=true)
```

Precedence, lowest to highest:

```
defaults < json < toml < .env files < environment variables
```

### 2. Retry a flaky call

```python
from handy import retry

@retry(on=ConnectionError, attempts=5, backoff=0.2, jitter=True)
def call_api():
    ...
```

### 3. Cache an expensive result

```python
from handy import ttl_cache

@ttl_cache(seconds=30)
def get_quote(symbol: str):
    ...
```

### 4. Throttle outgoing requests

```python
from handy import RateLimiter

limiter = RateLimiter(calls=10, period=1.0)
if limiter.try_acquire():
    send_request()
```

## Running the tests

```bash
python -m unittest discover -s tests -v
```

The suite uses only the standard library — no `pytest` required.
