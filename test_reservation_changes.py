"""Synthetic tests for offline reservation change policy."""
import unittest
from datetime import datetime, timedelta, timezone
from reservation_availability import Table
from reservation_changes import Reservation, amend_reservation, cancel_reservation

T = datetime(2026, 11, 16, 18, tzinfo=timezone.utc)
H = timedelta(hours=1)
TABLES = (Table('a', 't1', 2), Table('a', 't2', 4), Table('b', 't1', 10))
B = Reservation('a', 'r1', 't1', T, T + H, 'confirmed', 0, 2)
O = Reservation('a', 'r2', 't2', T, T + H, 'confirmed', 0, 2)


class ChangesTests(unittest.TestCase):
    def change(self, **kwargs):
        args = dict(booking=B, expected_revision=0, venue_id='a', new_table_id='t1',
                    new_start=T + timedelta(hours=2), duration=H,
                    turnover=timedelta(minutes=15), tables=TABLES, reservations=(B, O))
        args.update(kwargs)
        return amend_reservation(**args)

    def test_success_and_revision(self):
        result = self.change()
        self.assertEqual((result.revision, result.ends_at), (1, T + 3 * H))
        self.assertEqual(B.revision, 0)

    def test_conflict_and_turnover(self):
        with self.assertRaises(ValueError):
            self.change(new_table_id='t2', new_start=T + H)

    def test_cross_venue_and_stale(self):
        for kw in ({'venue_id': 'b'}, {'expected_revision': 1}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                self.change(**kw)

    def test_seated_and_missing_authority(self):
        with self.assertRaises(ValueError):
            self.change(booking=Reservation('a', 'r1', 't1', T, T + H, 'seated', 0, 2))
        with self.assertRaises(ValueError):
            self.change(reservations=(O,))

    def test_cancel_and_double_cancel(self):
        cancelled = cancel_reservation(booking=B, expected_revision=0, venue_id='a')
        self.assertEqual((cancelled.status, cancelled.revision), ('cancelled', 1))
        with self.assertRaises(ValueError):
            cancel_reservation(booking=cancelled, expected_revision=1, venue_id='a')

    def test_cancel_tenant_and_revision(self):
        for venue, revision in [('b', 0), ('a', 1)]:
            with self.assertRaises(ValueError):
                cancel_reservation(booking=B, expected_revision=revision, venue_id=venue)


if __name__ == '__main__':
    unittest.main()
