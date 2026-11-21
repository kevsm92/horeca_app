"""Synthetic tests for read-only waitlist candidate selection."""
import sqlite3
import unittest
from reservation_waitlist_sqlite import initialize_waitlist, enroll, withdraw
from reservation_waitlist_candidates import rank_candidates

T = '2026-11-18T19:00:00+00:00'

class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize_waitlist(self.db)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def add(self, venue, request, party, time=T):
        enroll(self.db, venue_id=venue, request_id=request, party_size=party, start_utc=time)

    def rank(self, **kwargs):
        return rank_candidates(self.db, venue_id='a', available_seats=4,
                               not_after_utc=T, **kwargs)

    def test_stable_order_and_limit(self):
        self.add('a','z',2)
        self.add('a','b',3,'2026-11-18T18:00:00+00:00')
        self.add('a','c',2)
        self.assertEqual(['b','c','z'], [r['request_id'] for r in self.rank()])
        self.assertEqual(['b'], [r['request_id'] for r in self.rank(limit=1)])

    def test_capacity_cutoff_and_tenant_scope(self):
        self.add('a','large',5)
        self.add('a','future',2,'2026-11-18T20:00:00+00:00')
        self.add('b','other',2)
        self.add('a','fits',4)
        self.assertEqual(['fits'], [r['request_id'] for r in self.rank()])

    def test_withdrawal_and_read_only(self):
        self.add('a','one',2)
        self.add('a','two',2)
        withdraw(self.db, venue_id='a', request_id='one')
        before = self.db.total_changes
        self.assertEqual(['two'], [r['request_id'] for r in self.rank()])
        self.assertEqual(before, self.db.total_changes)

    def test_invalid_inputs(self):
        for seats in (True, 0, 101):
            with self.assertRaises(ValueError):
                rank_candidates(self.db, venue_id='a', available_seats=seats, not_after_utc=T)
        for cutoff in ('bad','2026-11-18T19:00:00','2026-11-18T20:00:00+01:00'):
            with self.assertRaises(ValueError):
                rank_candidates(self.db, venue_id='a', available_seats=4, not_after_utc=cutoff)
        with self.assertRaises(ValueError):
            self.rank(limit=0)
        with self.assertRaises(ValueError):
            rank_candidates(self.db, venue_id='', available_seats=4, not_after_utc=T)

if __name__ == '__main__':
    unittest.main()
