"""Synthetic SQLite regression checks for cancellation isolation and rollback."""
import sqlite3
import unittest
from reservation_cancel_sqlite import cancel_reservation, CancellationConflict

class CancellationIsolationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.db.execute('CREATE TABLE reservations(id TEXT, venue_id TEXT, status TEXT, revision INTEGER, PRIMARY KEY(venue_id,id))')
        self.db.executemany('INSERT INTO reservations VALUES(?,?,?,?)', [('r1','venue-a','confirmed',0),('r1','venue-b','confirmed',0)])
    def tearDown(self): self.db.close()
    def state(self, venue):
        return self.db.execute('SELECT status,revision FROM reservations WHERE venue_id=? AND id=?',(venue,'r1')).fetchone()
    def test_cancel_only_target_venue(self):
        self.assertEqual(cancel_reservation(self.db,venue_id='venue-a',reservation_id='r1',expected_revision=0),1)
        self.assertEqual(self.state('venue-a'),('cancelled',1))
        self.assertEqual(self.state('venue-b'),('confirmed',0))
    def test_stale_and_repeat_cancel_do_not_mutate(self):
        with self.assertRaises(CancellationConflict):
            cancel_reservation(self.db,venue_id='venue-a',reservation_id='r1',expected_revision=1)
        self.assertEqual(self.state('venue-a'),('confirmed',0))
        cancel_reservation(self.db,venue_id='venue-a',reservation_id='r1',expected_revision=0)
        with self.assertRaises(CancellationConflict):
            cancel_reservation(self.db,venue_id='venue-a',reservation_id='r1',expected_revision=1)
        self.assertEqual(self.state('venue-a'),('cancelled',1))
    def test_unknown_venue_cannot_cancel(self):
        with self.assertRaises(CancellationConflict):
            cancel_reservation(self.db,venue_id='venue-c',reservation_id='r1',expected_revision=0)
        self.assertEqual(self.state('venue-a'),('confirmed',0))
    def test_invalid_revision_and_active_transaction(self):
        for invalid in (True,-1,'0'):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                cancel_reservation(self.db,venue_id='venue-a',reservation_id='r1',expected_revision=invalid)
        self.db.execute('BEGIN')
        try:
            with self.assertRaises(ValueError):
                cancel_reservation(self.db,venue_id='venue-a',reservation_id='r1',expected_revision=0)
            self.assertTrue(self.db.in_transaction)
        finally: self.db.rollback()
        self.assertEqual(self.state('venue-a'),('confirmed',0))

if __name__ == '__main__': unittest.main()
