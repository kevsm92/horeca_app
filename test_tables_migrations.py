"""Migration tests using synthetic table records only."""
import sqlite3
import unittest

from tables_migrations import migrate, CURRENT_VERSION
from tables_foundation import seat, close


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)

    def tearDown(self):
        self.db.close()

    def test_new_database_bootstraps_and_enforces_constraints(self):
        self.assertEqual(migrate(self.db), CURRENT_VERSION)
        self.db.execute("INSERT INTO physical_tables VALUES ('v1','t1',2)")
        seat(self.db, 's1', 'v1', 't1', 2)
        with self.assertRaises(sqlite3.IntegrityError):
            seat(self.db, 's2', 'v1', 't1', 1)

    def test_unversioned_existing_records_preserved(self):
        migrate(self.db)
        self.db.execute("INSERT INTO physical_tables VALUES ('v1','t1',3)")
        seat(self.db, 's1', 'v1', 't1', 2)
        self.db.execute('PRAGMA user_version=0')
        migrate(self.db)
        self.assertEqual(self.db.execute('SELECT guest_count FROM seating_sessions WHERE session_id=?', ('s1',)).fetchone()[0], 2)
        close(self.db, 's1', 'v1')

    def test_idempotent(self):
        self.assertEqual(migrate(self.db), 1)
        self.assertEqual(migrate(self.db), 1)

    def test_future_version_rejected_without_modification(self):
        self.db.execute('PRAGMA user_version=99')
        with self.assertRaises(ValueError):
            migrate(self.db)
        self.assertEqual(self.db.execute('PRAGMA user_version').fetchone()[0], 99)
        self.assertIsNone(self.db.execute("SELECT name FROM sqlite_master WHERE name='physical_tables'").fetchone())

    def test_active_transaction_rejected(self):
        self.db.execute('BEGIN')
        with self.assertRaises(ValueError):
            migrate(self.db)
        self.db.execute('ROLLBACK')


if __name__ == '__main__':
    unittest.main()
