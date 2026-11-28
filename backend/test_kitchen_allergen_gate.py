import unittest
from datetime import datetime, timezone
from kitchen_allergen_gate import review_allergen_warning, review_matches_ticket


class AllergenGateTests(unittest.TestCase):
    def setUp(self):
        self.args = dict(venue_id="fictional-a", actor_venue_id="fictional-a",
                         ticket_id="ticket-1", revision=3,
                         declared_allergens=("milk", "nuts"), actor_id="staff-fictional",
                         at=datetime(2026, 11, 26, 16, tzinfo=timezone.utc))

    def test_review_and_revision_binding(self):
        r = review_allergen_warning(**self.args)
        self.assertTrue(review_matches_ticket(r, venue_id="fictional-a", ticket_id="ticket-1",
                                              revision=3, declared_allergens=("milk", "nuts")))
        self.assertFalse(review_matches_ticket(r, venue_id="fictional-a", ticket_id="ticket-1",
                                               revision=4, declared_allergens=("milk", "nuts")))
        self.assertFalse(review_matches_ticket(r, venue_id="fictional-a", ticket_id="ticket-1",
                                               revision=3, declared_allergens=("milk",)))
        self.assertEqual(r.reviewed_at, "2026-11-26T16:00:00+00:00")

    def test_cross_venue_denied(self):
        with self.assertRaises(PermissionError):
            review_allergen_warning(**{**self.args, "actor_venue_id": "fictional-b"})

    def test_missing_warning_denied(self):
        with self.assertRaises(ValueError):
            review_allergen_warning(**{**self.args, "declared_allergens": ()})

    def test_naive_time_denied(self):
        with self.assertRaises(ValueError):
            review_allergen_warning(**{**self.args, "at": datetime(2026, 11, 26)})

    def test_invalid_revision_denied(self):
        with self.assertRaises(ValueError):
            review_allergen_warning(**{**self.args, "revision": True})

    def test_duplicate_warning_denied(self):
        with self.assertRaises(ValueError):
            review_allergen_warning(**{**self.args, "declared_allergens": ("milk", "milk")})


if __name__ == "__main__":
    unittest.main()
