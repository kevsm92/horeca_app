"""Synthetic waitlist withdrawal regression tests, file-backed SQLite."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from reservation_waitlist_sqlite import initialize_waitlist, enroll, withdraw, WaitlistConflict

T = '2026-11-18T19:00:00+00:00'

class WithdrawalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        path = str(Path(self.tmp.name) / 'waitlist.sqlite')
        self.a = sqlite3.connect(path, timeout=1)
        self.b = sqlite3.connect(path, timeout=1)
        initialize_waitlist(self.a)
        self.a.commit()
        enroll(self.a, venue_id='v1', request_id='r1', party_size=2, start_utc=T)
        enroll(self.a, venue_id='v2', request_id='r1', party_size=3, start_utc=T)

    def tearDown(self):
        self.a.close()
        self.b.close()
        self.tmp.cleanup()

    def test_withdraw_and_replay_across_connections(self):
        self.assertTrue(withdraw(self.a, venue_id='v1', request_id='r1'))
        self.assertFalse(withdraw(self.b, venue_id='v1', request_id='r1'))
        self.assertEqual('withdrawn', self.b.execute("SELECT status FROM reservation_waitlist WHERE venue_id='v1'").fetchone()[0])

    def test_venue_isolation(self):
        withdraw(self.a, venue_id='v1', request_id='r1')
        self.assertEqual('waiting', self.b.execute("SELECT status FROM reservation_waitlist WHERE venue_id='v2'").fetchone()[0])
        with self.assertRaises(WaitlistConflict):
            withdraw(self.b, venue_id='v3', request_id='r1')
        self.assertFalse(self.b.in_transaction)

    def test_missing_request_and_invalid_identifiers(self):
        with self.assertRaises(WaitlistConflict):
            withdraw(self.a, venue_id='v1', request_id='unknown')
        for venue, request in (('', 'r1'), ('v1', ''), (None, 'r1'), ('v1', None)):
            with self.assertRaises(ValueError):
                withdraw(self.a, venue_id=venue, request_id=request)
        self.assertFalse(self.a.in_transaction)

    def test_rejects_existing_transaction_without_mutation(self):
        self.a.execute('BEGIN')
        with self.assertRaises(ValueError):
            withdraw(self.a, venue_id='v1', request_id='r1')
        self.a.rollback()
        self.assertEqual('waiting', self.b.execute("SELECT status FROM reservation_waitlist WHERE venue_id='v1'").fetchone()[0])

    def test_withdrawn_entry_cannot_reenroll(self):
        withdraw(self.a, venue_id='v1', request_id='r1')
        with self.assertRaises(WaitlistConflict):
            enroll(self.b, venue_id='v1', request_id='r1', party_size=2, start_utc=T)

if __name__ == '__main__':
    unittest.main()
