"""Offline reservation waitlist prototype; synthetic data only.

Run: python -m unittest discover -s prototypes -p 'test_waitlist_*.py'
Not wired to an API or database. Production requires transactional locking and RBAC.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import unittest


@dataclass(frozen=True)
class Entry:
    id: str
    venue_id: str
    guests: int
    requested_at: datetime
    status: str = "waiting"


def eligible_waitlist(entries, venue_id, available_seats):
    """Return waiting entries in FIFO order without bypassing tenant or capacity."""
    if not isinstance(available_seats, int) or isinstance(available_seats, bool) or available_seats < 1:
        raise ValueError("available_seats must be positive integer")
    selected = []
    seen = set()
    for entry in sorted(entries, key=lambda e: (e.requested_at, e.id)):
        if entry.id in seen:
            raise ValueError("duplicate waitlist entry ID")
        seen.add(entry.id)
        if entry.guests < 1 or not isinstance(entry.guests, int) or isinstance(entry.guests, bool):
            raise ValueError("invalid guest count")
        if entry.requested_at.tzinfo is None or entry.requested_at.utcoffset() is None:
            raise ValueError("timezone-aware timestamp required")
        if entry.venue_id == venue_id and entry.status == "waiting" and entry.guests <= available_seats:
            selected.append(entry)
    return selected


class WaitlistTests(unittest.TestCase):
    def setUp(self):
        self.t = datetime(2026, 11, 16, tzinfo=timezone.utc)

    def test_fifo_tie_break(self):
        entries = [Entry("b", "v1", 2, self.t), Entry("a", "v1", 2, self.t)]
        self.assertEqual([e.id for e in eligible_waitlist(entries, "v1", 2)], ["a", "b"])

    def test_tenant_and_status_isolation(self):
        entries = [Entry("a", "other", 2, self.t), Entry("b", "v1", 2, self.t, "cancelled"), Entry("c", "v1", 2, self.t)]
        self.assertEqual([e.id for e in eligible_waitlist(entries, "v1", 2)], ["c"])

    def test_capacity(self):
        self.assertEqual(eligible_waitlist([Entry("a", "v1", 5, self.t)], "v1", 4), [])

    def test_reject_duplicate_ids(self):
        with self.assertRaises(ValueError):
            eligible_waitlist([Entry("a", "v1", 2, self.t)] * 2, "v1", 2)

    def test_reject_invalid_capacity(self):
        for seats in (0, -1, True, 1.5):
            with self.subTest(seats=seats), self.assertRaises(ValueError):
                eligible_waitlist([], "v1", seats)

    def test_reject_naive_timestamp(self):
        with self.assertRaises(ValueError):
            eligible_waitlist([Entry("a", "v1", 2, datetime(2026, 11, 16))], "v1", 2)

    def test_reject_invalid_guest_count(self):
        for guests in (0, -1, True, 1.5):
            with self.subTest(guests=guests), self.assertRaises(ValueError):
                eligible_waitlist([Entry("a", "v1", guests, self.t)], "v1", 2)


if __name__ == "__main__":
    unittest.main()
