"""Synthetic offline regression checks for manual no-show review."""
import unittest
from reservation_no_show_review import review_candidates

NOW = "2026-11-16T18:00:00+00:00"


def booking(id, venue="a", status="confirmed", time="2026-11-16T17:45:00+00:00", revision=2):
    return dict(id=id, venue_id=venue, status=status, scheduled_utc=time, revision=revision)


class ReviewTests(unittest.TestCase):
    def review(self, rows):
        return review_candidates(venue_id="a", reservations=rows, now_utc=NOW, grace_minutes=15)

    def test_boundary_and_no_mutation(self):
        rows = [booking("x")]
        self.assertEqual(self.review(rows), [{"reservation_id": "x", "expected_revision": 2,
                         "scheduled_utc": "2026-11-16T17:45:00+00:00", "staff_review_required": True}])
        self.assertEqual(rows[0]["status"], "confirmed")

    def test_tenant_and_status_filter(self):
        self.assertEqual(self.review([booking("secret", venue="b", time="invalid"),
                         booking("cancel", status="cancelled"),
                         booking("future", time="2026-11-16T17:46:00+00:00")]), [])

    def test_order(self):
        self.assertEqual([x["reservation_id"] for x in self.review([booking("z"), booking("a")])], ["a", "z"])

    def test_duplicate_confirmed_ids_fail_closed_even_if_future(self):
        with self.assertRaisesRegex(ValueError, "duplicate reservation"):
            self.review([booking("same"), booking("same", time="2026-11-16T20:00:00+00:00")])

    def test_other_venue_duplicate_id_is_not_a_collision(self):
        self.assertEqual(len(self.review([booking("same"), booking("same", venue="b")])), 1)

    def test_invalid_future_booking_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "invalid trusted booking"):
            self.review([booking("future", time="2026-11-16T20:00:00+00:00", revision=True)])

    def test_reject_invalid(self):
        for now in ["2026-11-16T18:00:00", "2026-11-16T19:00:00+01:00"]:
            with self.assertRaises(ValueError):
                review_candidates(venue_id="a", reservations=[], now_utc=now, grace_minutes=15)
        for grace in [True, -1, 1441, 1.5]:
            with self.assertRaises(ValueError):
                review_candidates(venue_id="a", reservations=[], now_utc=NOW, grace_minutes=grace)


if __name__ == "__main__":
    unittest.main()
