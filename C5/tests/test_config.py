"""Tests for handy.config — layered configuration loading."""

import os
import unittest
from pathlib import Path

from handy import Config, load_config


class TestConfigAccess(unittest.TestCase):
    def test_dot_access(self):
        cfg = Config({"db": {"host": "localhost", "port": 5432}})
        self.assertEqual(cfg.get("db.host"), "localhost")
        self.assertEqual(cfg.get("db.port"), 5432)
        self.assertIsNone(cfg.get("missing"))
        self.assertEqual(cfg.get("missing", "default"), "default")

    def test_require_raises(self):
        cfg = Config({})
        with self.assertRaises(KeyError):
            cfg.require("nope")

    def test_contains(self):
        cfg = Config({"a": 1})
        self.assertIn("a", cfg)
        self.assertNotIn("b", cfg)


class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = Path("tests/_tmp")
        self.tmp.mkdir(exist_ok=True)

    def tearDown(self):
        for p in self.tmp.glob("*"):
            p.unlink()
        self.tmp.rmdir()

    def test_defaults_only(self):
        cfg = load_config({"debug": False})
        self.assertFalse(cfg.get("debug"))

    def test_json_overlay(self):
        p = self.tmp / "c.json"
        p.write_text('{"db": {"host": "json-host"}}', encoding="utf-8")
        cfg = load_config({"db": {"host": "default", "port": 1}}, json_path=p)
        self.assertEqual(cfg.get("db.host"), "json-host")
        self.assertEqual(cfg.get("db.port"), 1)

    def test_env_overlay_with_prefix_and_coercion(self):
        os.environ["APP_DEBUG"] = "true"
        os.environ["APP_DB__PORT"] = "9999"
        try:
            cfg = load_config(
                {"debug": False, "db": {"port": 1}}, env_prefix="APP_"
            )
            self.assertTrue(cfg.get("debug"))
            self.assertEqual(cfg.get("db.port"), 9999)
        finally:
            del os.environ["APP_DEBUG"]
            del os.environ["APP_DB__PORT"]


if __name__ == "__main__":
    unittest.main()
