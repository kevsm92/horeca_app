"""Focused synthetic checks for offline inspection review."""
import unittest
from dataclasses import replace
from inspection_review import InspectionReviews, Observation

class InspectionReviewTests(unittest.TestCase):
    def setUp(self):
        self.store = InspectionReviews()
        self.obs = Observation("venue-a", "check-1", "fridge-temp", 2,
                               "worker-1", "2026-11-24T04:00:00Z", "fail", "9.1", "C")
        self.store.record(self.obs)

    def test_tenant_isolation(self):
        self.assertEqual(self.store.history(venue_id="venue-b", check_id="check-1"), ())
        with self.assertRaises(ValueError):
            self.store.review(venue_id="venue-b", check_id="check-1", reviewer_id="mgr",
                              reviewed_at="2026-11-24T05:00:00Z", decision="needs_action", note="Investigate")

    def test_failed_check_cannot_be_verified(self):
        with self.assertRaises(ValueError):
            self.store.review(venue_id="venue-a", check_id="check-1", reviewer_id="mgr",
                              reviewed_at="2026-11-24T05:00:00Z", decision="verified_record", note="No")

    def test_independent_review_and_immutable_history(self):
        with self.assertRaises(PermissionError):
            self.store.review(venue_id="venue-a", check_id="check-1", reviewer_id="worker-1",
                              reviewed_at="2026-11-24T05:00:00Z", decision="needs_action", note="Fix")
        self.store.review(venue_id="venue-a", check_id="check-1", reviewer_id="mgr",
                          reviewed_at="2026-11-24T05:00:00Z", decision="needs_action", note="Recheck")
        self.assertEqual(len(self.store.history(venue_id="venue-a", check_id="check-1")), 2)
        with self.assertRaises(ValueError):
            self.store.record(self.obs)
        with self.assertRaises(ValueError):
            self.store.review(venue_id="venue-a", check_id="check-1", reviewer_id="mgr",
                              reviewed_at="2026-11-24T05:01:00Z", decision="needs_action", note="Overwrite")

    def test_invalid_measurement_and_time(self):
        with self.assertRaises(ValueError):
            self.store.record(replace(self.obs, check_id="check-2", value=None))
        with self.assertRaises(ValueError):
            self.store.record(replace(self.obs, check_id="check-2", recorded_at="2026-11-24T04:00:00"))
        with self.assertRaises(ValueError):
            self.store.review(venue_id="venue-a", check_id="check-1", reviewer_id="mgr",
                              reviewed_at="2026-11-24T03:00:00Z", decision="needs_action", note="Earlier")

if __name__ == "__main__":
    unittest.main()
