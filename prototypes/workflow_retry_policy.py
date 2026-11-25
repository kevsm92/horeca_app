"""Deterministic offline retry policy for HORECA mock outbox workers.

This does not dispatch messages. A caller persists next_attempt_at in a future
migration and must use a venue-scoped lease before attempting delivery.
"""
from datetime import datetime, timedelta, timezone
import unittest


def next_retry_at(attempts, failed_at, *, base_seconds=30, cap_seconds=3600):
    """Return UTC retry instant after a failed attempt; attempts starts at 1."""
    if type(attempts) is not int or not 1 <= attempts <= 1000:
        raise ValueError("attempts must be an integer between 1 and 1000")
    if type(base_seconds) is not int or type(cap_seconds) is not int or not 1 <= base_seconds <= cap_seconds:
        raise ValueError("invalid retry limits")
    if not isinstance(failed_at, datetime) or failed_at.tzinfo is None or failed_at.utcoffset() is None:
        raise ValueError("failed_at must be timezone aware")
    delay = min(cap_seconds, base_seconds * (2 ** min(attempts - 1, 30)))
    return failed_at.astimezone(timezone.utc) + timedelta(seconds=delay)


class RetryPolicyTests(unittest.TestCase):
    def test_exponential_and_cap(self):
        t = datetime(2026, 11, 25, tzinfo=timezone.utc)
        self.assertEqual((next_retry_at(1, t)-t).total_seconds(), 30)
        self.assertEqual((next_retry_at(3, t)-t).total_seconds(), 120)
        self.assertEqual((next_retry_at(1000, t)-t).total_seconds(), 3600)

    def test_reject_invalid_and_naive_times(self):
        t = datetime(2026, 11, 25)
        for n in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                next_retry_at(n, datetime.now(timezone.utc))
        with self.assertRaises(ValueError):
            next_retry_at(1, t)
        with self.assertRaises(ValueError):
            next_retry_at(1, datetime.now(timezone.utc), base_seconds=60, cap_seconds=30)

    def test_no_randomness_or_side_effects(self):
        t = datetime(2026, 11, 25, tzinfo=timezone.utc)
        self.assertEqual(next_retry_at(4, t), next_retry_at(4, t))


if __name__ == "__main__":
    unittest.main()
