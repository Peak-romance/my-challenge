"""Demonstrates layered configuration loading.

Run with:  python examples/config_example.py
"""

from handy import load_config

config = load_config(
    defaults={"debug": False, "db": {"host": "localhost", "port": 5432}},
    env_prefix="APP_",
)

print("debug      :", config.get("debug"))
print("db.host    :", config.get("db.host"))
print("db.port    :", config.get("db.port"))
print("missing.key:", config.get("missing.key", "<<default>>"))
