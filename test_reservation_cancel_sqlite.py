import sqlite3
import unittest
from reservation_cancel_sqlite import cancel_reservation, CancellationConflict


class CancellationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('CREATE TABLE reservations (id TEXT PRIMARY KEY, venue_id TEXT NOT NULL, status TEXT NOT NULL, revision INTEGER NOT NULL)')
        self.db.execute("INSERT INTO reservations VALUES ('r1','v1','confirmed',2)")
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def state(self):
        return self.db.execute("SELECT status,revision FROM reservations WHERE id='r1'").fetchone()

    def test_success(self):
        self.assertEqual(cancel_reservation(self.db,venue_id='v1',reservation_id='r1',expected_revision=2),3)
        self.assertEqual(self.state(),('cancelled',3))

    def test_cross_tenant(self):
        with self.assertRaises(CancellationConflict):
            cancel_reservation(self.db,venue_id='v2',reservation_id='r1',expected_revision=2)
        self.assertEqual(self.state(),('confirmed',2))

    def test_stale_revision(self):
        with self.assertRaises(CancellationConflict):
            cancel_reservation(self.db,venue_id='v1',reservation_id='r1',expected_revision=1)
        self.assertEqual(self.state(),('confirmed',2))

    def test_repeat_is_not_silent_success(self):
        cancel_reservation(self.db,venue_id='v1',reservation_id='r1',expected_revision=2)
        with self.assertRaises(CancellationConflict):
            cancel_reservation(self.db,venue_id='v1',reservation_id='r1',expected_revision=3)

    def test_invalid_boolean_revision(self):
        with self.assertRaises(ValueError):
            cancel_reservation(self.db,venue_id='v1',reservation_id='r1',expected_revision=True)

    def test_no_nested_transaction(self):
        self.db.execute('BEGIN')
        with self.assertRaises(ValueError):
            cancel_reservation(self.db,venue_id='v1',reservation_id='r1',expected_revision=2)
        self.db.rollback()

if __name__ == '__main__':
    unittest.main()
