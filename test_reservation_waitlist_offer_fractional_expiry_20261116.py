"""Regression tests: UTC fractional seconds must not bypass active waitlist holds."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from reservation_waitlist_sqlite import initialize_waitlist, enroll
from reservation_waitlist_offers import initialize_offers, create_offer, OfferConflict


class FractionalExpiryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "offers.sqlite")
        self.a = sqlite3.connect(self.path, timeout=1)
        self.b = sqlite3.connect(self.path, timeout=1)
        for conn in (self.a, self.b):
            conn.execute("PRAGMA foreign_keys=ON")
        initialize_waitlist(self.a)
        initialize_offers(self.a)
        self.a.commit()
        for venue, request in (("a", "r1"), ("a", "r2"), ("b", "r1")):
            enroll(self.a, venue_id=venue, request_id=request, party_size=2,
                   start_utc="2026-11-16T18:00:00+00:00")

    def tearDown(self):
        self.a.close()
        self.b.close()
        self.tmp.cleanup()

    def offer(self, conn, **overrides):
        args = dict(venue_id="a", offer_id="o1", request_id="r1",
                    table_id="t1", created_utc="2026-11-16T18:00:00+00:00",
                    expires_utc="2026-11-16T18:15:00+00:00")
        args.update(overrides)
        return create_offer(conn, **args)

    def test_fractional_expiry_still_blocks_at_whole_second(self):
        self.offer(self.a, expires_utc="2026-11-16T18:15:00.500000+00:00")
        with self.assertRaises(OfferConflict):
            self.offer(self.b, offer_id="o2", request_id="r2",
                       created_utc="2026-11-16T18:15:00+00:00",
                       expires_utc="2026-11-16T18:30:00+00:00")

    def test_exact_expiry_allows_new_offer(self):
        self.offer(self.a, expires_utc="2026-11-16T18:15:00.500000+00:00")
        self.assertTrue(self.offer(
            self.b, offer_id="o2", request_id="r2",
            created_utc="2026-11-16T18:15:00.500000+00:00",
            expires_utc="2026-11-16T18:30:00+00:00"))

    def test_same_request_blocked(self):
        self.offer(self.a)
        with self.assertRaises(OfferConflict):
            self.offer(self.b, offer_id="o2", table_id="t2")

    def test_venue_isolation(self):
        self.offer(self.a)
        self.assertTrue(self.offer(self.b, venue_id="b"))


if __name__ == "__main__":
    unittest.main()
