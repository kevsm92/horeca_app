"""Synthetic SQLite tests for table capacity compare-and-swap."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from table_capacity_cas import change_table_capacity

SCHEMA = """
CREATE TABLE physical_tables(venue_id TEXT NOT NULL,table_id TEXT NOT NULL,
 capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 100),PRIMARY KEY(venue_id,table_id));
CREATE TABLE seating_sessions(session_id TEXT PRIMARY KEY,venue_id TEXT NOT NULL,
 table_id TEXT NOT NULL,guest_count INTEGER NOT NULL,status TEXT NOT NULL,
 FOREIGN KEY(venue_id,table_id) REFERENCES physical_tables(venue_id,table_id));
CREATE UNIQUE INDEX one_active_session_per_table ON seating_sessions(venue_id,table_id)
 WHERE status='active';
CREATE TRIGGER prevent_capacity_below_active_guests BEFORE UPDATE OF capacity ON physical_tables
 BEGIN SELECT RAISE(ABORT,'active guests exceed capacity') WHERE NEW.capacity <
 COALESCE((SELECT guest_count FROM seating_sessions WHERE venue_id=OLD.venue_id
 AND table_id=OLD.table_id AND status='active'),0); END;
"""

class CapacityCASTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / 'tables.sqlite')
        self.db = sqlite3.connect(self.path, isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript(SCHEMA)
        self.db.executemany('INSERT INTO physical_tables VALUES (?,?,?)',
                            [('venue-a','t1',6),('venue-b','t1',8)])

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def capacity(self, venue='venue-a'):
        return self.db.execute('SELECT capacity FROM physical_tables WHERE venue_id=? AND table_id=?',
                               (venue,'t1')).fetchone()[0]

    def test_valid_change_preserves_other_venue(self):
        change_table_capacity(self.db,'venue-a','t1',6,4)
        self.assertEqual((self.capacity(),self.capacity('venue-b')),(4,8))

    def test_active_guests_prevent_shrink_and_rollback(self):
        self.db.execute("INSERT INTO seating_sessions VALUES ('s','venue-a','t1',5,'active')")
        with self.assertRaises(ValueError):
            change_table_capacity(self.db,'venue-a','t1',6,4)
        self.assertEqual(self.capacity(),6)
        self.assertFalse(self.db.in_transaction)

    def test_stale_capacity_and_unknown_table_rejected(self):
        for table, expected in [('t1',5),('missing',6)]:
            with self.subTest(table=table), self.assertRaises(ValueError):
                change_table_capacity(self.db,'venue-a',table,expected,4)
        self.assertEqual(self.capacity(),6)

    def test_reject_boolean_and_out_of_range(self):
        for value in [True,0,101,2.0,'4']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                change_table_capacity(self.db,'venue-a','t1',6,value)
        self.assertEqual(self.capacity(),6)

    def test_concurrent_stale_writer_cannot_overwrite(self):
        other = sqlite3.connect(self.path,isolation_level=None)
        try:
            change_table_capacity(self.db,'venue-a','t1',6,5)
            with self.assertRaises(ValueError):
                change_table_capacity(other,'venue-a','t1',6,4)
            self.assertEqual(self.capacity(),5)
        finally:
            other.close()

if __name__ == '__main__':
    unittest.main()
