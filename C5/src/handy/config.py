"""Layered configuration with a predictable precedence order.

Precedence (lowest to highest)::

    defaults  <  json file  <  toml file  <  .env files  <  environment variables

All layers are deep-merged. Environment variables are matched by an optional
prefix (e.g. ``APP_``) and support nested keys via a double-underscore
separator, so ``APP_DB__HOST=localhost`` maps to ``db.host``. When an incoming
environment value overlaps an existing boolean/int/float default, it is coerced
to that type automatically.

This module uses only the Python standard library. TOML support requires
Python 3.11+ (``tomllib``); on older interpreters passing ``toml_path`` raises
a clear ``RuntimeError`` rather than failing silently.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Optional

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _deep_merge(base: MutableMapping[str, Any], over: Mapping[str, Any]) -> None:
    """Recursively merge ``over`` into ``base`` in place."""
    for key, value in over.items():
        if (
            key in base
            and isinstance(base[key], MutableMapping)
            and isinstance(value, Mapping)
        ):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _read_toml(path: Path) -> dict[str, Any]:
    if tomllib is None:  # pragma: no cover
        raise RuntimeError("TOML support requires Python 3.11+ (tomllib).")
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_env_file(path: Path) -> dict[str, Any]:
    """Parse a trivial ``KEY=VALUE`` ``.env`` file (no quoting gymnastics)."""
    data: dict[str, Any] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _coerce(value: str, existing: Any) -> Any:
    """Coerce a string env value to the type of an existing default."""
    if isinstance(existing, bool):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(existing, int):
        try:
            return int(value)
        except ValueError:
            return value
    if isinstance(existing, float):
        try:
            return float(value)
        except ValueError:
            return value
    return value


def _assign_dotted(target: MutableMapping[str, Any], key: str, value: Any) -> None:
    """Assign ``value`` at a dot/``__`` nested ``key`` within ``target``."""
    parts = key.split("__") if "__" in key else key.split(".")
    node: Any = target
    for part in parts[:-1]:
        nxt = node.get(part)
        if not isinstance(nxt, MutableMapping):
            nxt = {}
            node[part] = nxt
        node = nxt
    last = parts[-1]
    if last in node and isinstance(value, str):
        value = _coerce(value, node[last])
    node[last] = value


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
class Config:
    """Read-only view over a merged configuration mapping.

    Nested values are reached with dot-notation keys such as ``"db.host"``.
    """

    def __init__(self, data: Mapping[str, Any]) -> None:
        self._data: dict[str, Any] = dict(data)

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value at ``key`` (dot notation) or ``default``."""
        node: Any = self._data
        for part in key.split("."):
            if isinstance(node, Mapping) and part in node:
                node = node[part]
            else:
                return default
        return node

    def require(self, key: str) -> Any:
        """Return the value at ``key`` or raise ``KeyError`` if absent."""
        value = self.get(key)
        if value is None:
            raise KeyError(f"Required configuration key missing: {key!r}")
        return value

    def as_dict(self) -> dict[str, Any]:
        """Return a shallow copy of the underlying mapping."""
        return dict(self._data)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def __repr__(self) -> str:  # pragma: no cover
        return f"Config({self._data!r})"


def load_config(
    defaults: Optional[Mapping[str, Any]] = None,
    *,
    json_path: Optional[Any] = None,
    toml_path: Optional[Any] = None,
    env_prefix: str = "",
    env_files: Iterable[Any] = (".env",),
) -> Config:
    """Build a :class:`Config` by layering multiple sources.

    Parameters
    ----------
    defaults:
        Baseline mapping with the lowest precedence.
    json_path / toml_path:
        Optional files overlaid on top of ``defaults``.
    env_prefix:
        Only environment variables (and ``.env`` keys) starting with this
        prefix are injected. The prefix is stripped, the remainder is
        lower-cased, and ``__`` becomes a nested separator.
    env_files:
        ``.env``-style files evaluated just below real environment variables.

    Examples
    --------
    >>> cfg = load_config({"debug": False}, env_prefix="APP_")
    >>> cfg.get("debug")
    False
    """
    merged: dict[str, Any] = {}
    if defaults:
        _deep_merge(merged, defaults)

    if json_path:
        _deep_merge(merged, _read_json(Path(json_path)))
    if toml_path:
        _deep_merge(merged, _read_toml(Path(toml_path)))

    def _normalize(key: str) -> str:
        stripped = key[len(env_prefix):] if env_prefix else key
        return stripped.lower()

    for env_file in env_files:
        for key, value in _read_env_file(Path(env_file)).items():
            if env_prefix and not key.startswith(env_prefix):
                continue
            _assign_dotted(merged, _normalize(key), value)

    for key, value in os.environ.items():
        if env_prefix and not key.startswith(env_prefix):
            continue
        _assign_dotted(merged, _normalize(key), value)

    return Config(merged)
