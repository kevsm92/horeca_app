"""Connection bootstrap regression tests with synthetic persistent SQLite files."""
import os
import sqlite3
import tempfile
import unittest

from tables_foundation import connect, seat


class ConnectionMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "tables.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_file_is_versioned_and_usable(self):
        with connect(self.path) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
            db.execute("INSERT INTO physical_tables VALUES ('v1','t1',2)")
            seat(db, "s1", "v1", "t1", 2)

    def test_reopen_preserves_seating_and_schema_version(self):
        with connect(self.path) as db:
            db.execute("INSERT INTO physical_tables VALUES ('v1','t1',2)")
            seat(db, "s1", "v1", "t1", 2)
        with connect(self.path) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT guest_count FROM seating_sessions WHERE session_id='s1'").fetchone(), (2,))

    def test_future_schema_is_rejected_without_downgrade(self):
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA user_version=99")
        with self.assertRaises(ValueError):
            connect(self.path)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 99)
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='physical_tables'").fetchone())

    def test_unversioned_existing_file_is_upgraded_without_data_loss(self):
        with connect(self.path) as db:
            db.execute("INSERT INTO physical_tables VALUES ('v1','t1',3)")
            seat(db, "s1", "v1", "t1", 2)
            db.execute("PRAGMA user_version=0")
        with connect(self.path) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT guest_count FROM seating_sessions WHERE session_id='s1'").fetchone(), (2,))


if __name__ == "__main__":
    unittest.main()
