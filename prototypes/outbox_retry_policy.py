"""Offline retry scheduling for the venue-scoped SQLite workflow outbox.

Policy only: a later migration must persist next_attempt_at and review state.
No network delivery, live task creation, or background worker is enabled.
"""
from datetime import datetime, timedelta, timezone
import unittest

MAX_ATTEMPTS = 6
BASE_SECONDS = 30
MAX_DELAY_SECONDS = 900


def next_retry(attempts: int, failed_at: datetime):
    """Return ('retry', UTC ISO timestamp) or ('review_required', None)."""
    if type(attempts) is not int or attempts < 1:
        raise ValueError("attempts must be a positive integer")
    if not isinstance(failed_at, datetime) or failed_at.tzinfo is None or failed_at.utcoffset() is None:
        raise ValueError("failed_at must be timezone-aware")
    if attempts >= MAX_ATTEMPTS:
        return ("review_required", None)
    delay = min(BASE_SECONDS * 2 ** (attempts - 1), MAX_DELAY_SECONDS)
    return ("retry", (failed_at.astimezone(timezone.utc) + timedelta(seconds=delay)).isoformat())


class RetryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.t = datetime(2026, 11, 25, 5, 0, tzinfo=timezone.utc)

    def test_exponential_delays_and_terminal_review(self):
        self.assertEqual([next_retry(n, self.t)[1] for n in range(1, 6)],
                         [(self.t + timedelta(seconds=s)).isoformat() for s in (30, 60, 120, 240, 480)])
        self.assertEqual(next_retry(6, self.t), ("review_required", None))
        self.assertEqual(next_retry(100000, self.t), ("review_required", None))

    def test_timezone_normalized(self):
        local = self.t.astimezone(timezone(timedelta(hours=1)))
        self.assertEqual(next_retry(1, local), next_retry(1, self.t))

    def test_reject_invalid_inputs(self):
        for value in (0, -1, True, 1.5, "2"):
            with self.assertRaises(ValueError):
                next_retry(value, self.t)
        with self.assertRaises(ValueError):
            next_retry(1, datetime(2026, 11, 25))


if __name__ == "__main__":
    unittest.main()
