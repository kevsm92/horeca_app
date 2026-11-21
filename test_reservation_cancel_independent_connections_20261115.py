"""File-backed cancellation races with synthetic data and separate SQLite connections."""
import os
import sqlite3
import tempfile
import threading
import unittest

from reservation_cancel_sqlite import CancellationConflict, cancel_reservation


class IndependentCancellationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'reservations.sqlite3')
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE reservations (
                    id TEXT PRIMARY KEY, venue_id TEXT NOT NULL,
                    status TEXT NOT NULL, revision INTEGER NOT NULL);
                INSERT INTO reservations VALUES ('r1','venue-a','confirmed',0);
                INSERT INTO reservations VALUES ('r2','venue-b','confirmed',0);
            """)

    def tearDown(self):
        self.tmp.cleanup()

    def connect(self):
        return sqlite3.connect(self.path, timeout=3, isolation_level=None)

    def test_second_connection_cannot_cancel_stale_revision(self):
        with self.connect() as first, self.connect() as second:
            self.assertEqual(cancel_reservation(first, venue_id='venue-a', reservation_id='r1', expected_revision=0), 1)
            with self.assertRaises(CancellationConflict):
                cancel_reservation(second, venue_id='venue-a', reservation_id='r1', expected_revision=0)
            self.assertEqual(second.execute("SELECT status,revision FROM reservations WHERE id='r1'").fetchone(), ('cancelled', 1))
            self.assertEqual(second.execute("SELECT status,revision FROM reservations WHERE id='r2'").fetchone(), ('confirmed', 0))

    def test_writer_lock_serializes_cancellation_and_preserves_other_venue(self):
        started = threading.Event()
        outcomes = []
        with self.connect() as first:
            first.execute('BEGIN IMMEDIATE')
            first.execute("UPDATE reservations SET status='cancelled', revision=1 WHERE id='r1'")

            def contender():
                with self.connect() as second:
                    started.set()
                    try:
                        cancel_reservation(second, venue_id='venue-a', reservation_id='r1', expected_revision=0)
                        outcomes.append('unexpected-success')
                    except CancellationConflict:
                        outcomes.append('conflict')
                    except Exception as exc:
                        outcomes.append(type(exc).__name__)

            worker = threading.Thread(target=contender)
            worker.start()
            try:
                self.assertTrue(started.wait(2))
                self.assertEqual(outcomes, [])
                first.commit()
                worker.join(3)
                self.assertFalse(worker.is_alive())
                self.assertEqual(outcomes, ['conflict'])
                self.assertEqual(first.execute("SELECT status,revision FROM reservations WHERE id='r2'").fetchone(), ('confirmed', 0))
            finally:
                if first.in_transaction:
                    first.rollback()
                worker.join(3)


if __name__ == '__main__':
    unittest.main()
