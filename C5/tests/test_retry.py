"""Tests for handy.retry — retry decorator."""

import unittest

from handy import retry


class TestRetry(unittest.TestCase):
    def test_succeeds_after_failures(self):
        calls = {"n": 0}

        @retry(on=ValueError, attempts=3, backoff=0)
        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ValueError("boom")
            return "ok"

        self.assertEqual(flaky(), "ok")
        self.assertEqual(calls["n"], 3)

    def test_reraises_after_exhausting(self):
        @retry(on=ValueError, attempts=2, backoff=0)
        def always_fail():
            raise ValueError("nope")

        with self.assertRaises(ValueError):
            always_fail()

    def test_does_not_retry_other_exceptions(self):
        @retry(on=ValueError, attempts=5, backoff=0)
        def wrong_type():
            raise KeyError("different")

        with self.assertRaises(KeyError):
            wrong_type()

    def test_callback_invoked(self):
        seen = []

        @retry(on=Exception, attempts=2, backoff=0,
               on_retry=lambda a, e: seen.append(a))
        def fail():
            raise RuntimeError("x")

        with self.assertRaises(RuntimeError):
            fail()
        self.assertEqual(seen, [1])


if __name__ == "__main__":
    unittest.main()
