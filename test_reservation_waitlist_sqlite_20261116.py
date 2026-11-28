"""Synthetic, offline waitlist tests."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from reservation_waitlist_sqlite import initialize_waitlist, enroll, WaitlistConflict

T = '2026-11-18T19:00:00+00:00'


class WaitlistTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / 'waitlist.sqlite')
        self.a = sqlite3.connect(self.path, timeout=2)
        self.b = sqlite3.connect(self.path, timeout=2)
        initialize_waitlist(self.a)
        self.a.commit()

    def tearDown(self):
        self.a.close()
        self.b.close()
        self.tmp.cleanup()

    def test_replay_and_cross_connection(self):
        args = dict(venue_id='v1', request_id='r1', party_size=2, start_utc=T)
        self.assertTrue(enroll(self.a, **args))
        self.assertFalse(enroll(self.b, **args))
        self.assertEqual(1, self.a.execute('SELECT count(*) FROM reservation_waitlist').fetchone()[0])

    def test_tenant_scoped_request_ids(self):
        for venue in ('v1', 'v2'):
            self.assertTrue(enroll(self.a, venue_id=venue, request_id='same', party_size=2, start_utc=T))
        self.assertEqual(2, self.b.execute('SELECT count(*) FROM reservation_waitlist').fetchone()[0])

    def test_conflicting_replay_rolls_back(self):
        enroll(self.a, venue_id='v1', request_id='r1', party_size=2, start_utc=T)
        with self.assertRaises(WaitlistConflict):
            enroll(self.b, venue_id='v1', request_id='r1', party_size=3, start_utc=T)
        self.assertFalse(self.b.in_transaction)

    def test_reject_invalid_inputs(self):
        for party in (0, True, 101):
            with self.assertRaises(ValueError):
                enroll(self.a, venue_id='v1', request_id='r', party_size=party, start_utc=T)
        for timestamp in ('2026-11-18T19:00:00', '2026-11-18T20:00:00+01:00', 'invalid'):
            with self.assertRaises(ValueError):
                enroll(self.a, venue_id='v1', request_id='r', party_size=2, start_utc=timestamp)

    def test_withdrawn_cannot_be_reenrolled(self):
        args = dict(venue_id='v1', request_id='r1', party_size=2, start_utc=T)
        enroll(self.a, **args)
        self.a.execute("UPDATE reservation_waitlist SET status='withdrawn'")
        self.a.commit()
        with self.assertRaises(WaitlistConflict):
            enroll(self.b, **args)


if __name__ == '__main__':
    unittest.main()
