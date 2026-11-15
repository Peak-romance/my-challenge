"""Tests for handy.cache — TTL memoization."""

import time
import unittest

from handy import ttl_cache


class TestTtlCache(unittest.TestCase):
    def test_caches_and_counts(self):
        calls = {"n": 0}

        @ttl_cache(seconds=10)
        def add(a, b):
            calls["n"] += 1
            return a + b

        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(calls["n"], 1)
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(calls["n"], 2)

    def test_expires(self):
        calls = {"n": 0}

        @ttl_cache(seconds=0.05)
        def val():
            calls["n"] += 1
            return calls["n"]

        self.assertEqual(val(), 1)
        time.sleep(0.1)
        self.assertEqual(val(), 2)
        self.assertEqual(calls["n"], 2)

    def test_cache_clear(self):
        @ttl_cache(seconds=10)
        def f():
            return 1

        f()
        f.cache_clear()
        self.assertEqual(f.cache_info()[0], 0)


if __name__ == "__main__":
    unittest.main()
