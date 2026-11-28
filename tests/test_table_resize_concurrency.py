"""Offline two-connection concurrency regression for the SQLite reference resize."""
import os
import sqlite3
import tempfile
import threading
import unittest
from prototypes.table_resize_atomic_sqlite import install, resize


class ResizeConcurrencyTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix='.sqlite3')
        os.close(fd)
        self.first = sqlite3.connect(self.path, isolation_level=None, timeout=2)
        self.first.execute('PRAGMA foreign_keys=ON')
        install(self.first)
        self.first.execute("INSERT INTO physical_tables VALUES ('venue-a','table-1',4,6,0)")

    def tearDown(self):
        self.first.close()
        os.unlink(self.path)

    def test_stale_second_writer_does_not_overwrite_first(self):
        second = sqlite3.connect(self.path, isolation_level=None, timeout=2)
        try:
            self.assertEqual(resize(self.first, 'venue-a', 'table-1', 0, 5), 1)
            with self.assertRaises(ValueError):
                resize(second, 'venue-a', 'table-1', 0, 6)
            self.assertEqual(second.execute('SELECT capacity_seats,revision FROM physical_tables').fetchone(), (5, 1))
        finally:
            second.close()

    def test_locked_writer_cannot_commit_until_first_transaction_finishes(self):
        entered = threading.Event()
        finished = threading.Event()
        results = []
        self.first.execute('BEGIN IMMEDIATE')
        self.first.execute("UPDATE physical_tables SET capacity_seats=5,revision=1 WHERE venue_id='venue-a'")

        def contender():
            db = sqlite3.connect(self.path, isolation_level=None, timeout=2)
            try:
                entered.set()
                try:
                    resize(db, 'venue-a', 'table-1', 0, 6)
                    results.append('unexpected-success')
                except ValueError:
                    results.append('stale-revision')
            finally:
                db.close()
                finished.set()

        thread = threading.Thread(target=contender)
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            self.assertFalse(finished.wait(0.1), 'writer bypassed transaction lock')
            self.first.commit()
            self.assertTrue(finished.wait(2))
            self.assertEqual(results, ['stale-revision'])
            self.assertEqual(self.first.execute('SELECT capacity_seats,revision FROM physical_tables').fetchone(), (5, 1))
        finally:
            if self.first.in_transaction:
                self.first.rollback()
            thread.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
