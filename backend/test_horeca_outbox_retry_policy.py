import unittest
from datetime import datetime, timedelta, timezone
from horeca_outbox_retry_policy import decide_retry


class RetryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 25, 9, tzinfo=timezone.utc)

    def test_backoff(self):
        for attempt, seconds in [(1, 30), (2, 60), (3, 120), (4, 240)]:
            result = decide_retry(attempt, self.now)
            self.assertEqual(result.status, "retry_pending")
            self.assertEqual(result.next_attempt_at, self.now + timedelta(seconds=seconds))

    def test_dead_letter(self):
        self.assertEqual(decide_retry(5, self.now).status, "dead_letter")
        self.assertIsNone(decide_retry(5, self.now).next_attempt_at)
        self.assertEqual(decide_retry(1, self.now, permanent=True).status, "dead_letter")

    def test_rejects_bad_inputs(self):
        for attempts in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                decide_retry(attempts, self.now)
        with self.assertRaises(ValueError):
            decide_retry(1, datetime(2026, 11, 25))
        with self.assertRaises(ValueError):
            decide_retry(1, self.now.replace(tzinfo=timezone(timedelta(hours=1))))
        with self.assertRaises(ValueError):
            decide_retry(1, self.now, permanent=1)


if __name__ == "__main__":
    unittest.main()
