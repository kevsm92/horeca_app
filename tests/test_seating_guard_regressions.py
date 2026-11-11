"""Offline SQLite table-occupancy guard regressions; synthetic data only."""
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SeatingGuardRegressions(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        for name in ('sqlite_seating_schema.sql', 'sqlite_capacity_guards.sql'):
            self.db.executescript((ROOT / 'reference' / 'tables' / name).read_text())
        self.db.executemany('INSERT INTO physical_tables VALUES (?,?,?,1)',
                            [('v1', 't1', 4), ('v2', 't1', 2)])
        self.db.execute("INSERT INTO seating_sessions VALUES ('v1','s1','t1',3,'active')")
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_direct_insert_over_capacity_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO seating_sessions VALUES ('v2','s2','t1',3,'active')")

    def test_direct_update_over_capacity_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE seating_sessions SET guest_count=5 WHERE venue_id='v1'")

    def test_capacity_reduction_below_occupancy_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE physical_tables SET capacity_seats=2 WHERE venue_id='v1'")
        self.assertEqual(self.db.execute("SELECT capacity_seats FROM physical_tables WHERE venue_id='v1'").fetchone()[0], 4)

    def test_deactivation_while_seated_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE physical_tables SET active=0 WHERE venue_id='v1'")

    def test_double_seating_direct_insert_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO seating_sessions VALUES ('v1','s2','t1',2,'active')")

    def test_close_then_reseat_is_allowed(self):
        self.db.execute("UPDATE seating_sessions SET state='closed' WHERE venue_id='v1'")
        self.db.execute("INSERT INTO seating_sessions VALUES ('v1','s2','t1',2,'active')")
        self.assertEqual(self.db.execute("SELECT count(*) FROM seating_sessions WHERE venue_id='v1' AND state='active'").fetchone()[0], 1)

    def test_venue_scoped_table_identity(self):
        self.db.execute("INSERT INTO seating_sessions VALUES ('v2','s2','t1',2,'active')")
        self.assertEqual(self.db.execute("SELECT count(*) FROM seating_sessions WHERE state='active'").fetchone()[0], 2)

    def test_inactive_table_rejects_direct_seating(self):
        self.db.execute("UPDATE physical_tables SET active=0 WHERE venue_id='v2'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO seating_sessions VALUES ('v2','s2','t1',1,'active')")


if __name__ == '__main__':
    unittest.main()
