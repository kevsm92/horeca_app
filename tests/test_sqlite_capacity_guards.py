"""Offline SQLite seating capacity regression tests; synthetic records only."""
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "reference/tables/sqlite_seating_schema.sql").read_text()
GUARDS = (ROOT / "reference/tables/sqlite_capacity_guards.sql").read_text()

class CapacityGuardTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA + "\n" + GUARDS)
        self.db.execute("INSERT INTO physical_tables VALUES ('v','t',4,1)")

    def seat(self, guests=2, state="active"):
        self.db.execute("INSERT INTO seating_sessions VALUES (?,?,?,?,?)", ("v","s","t",guests,state))

    def test_valid_seating(self):
        self.seat(4)

    def test_reject_overcapacity_insert(self):
        with self.assertRaises(sqlite3.IntegrityError): self.seat(5)

    def test_reject_capacity_reduction(self):
        self.seat(3)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE physical_tables SET capacity_seats=2 WHERE venue_id='v'")

    def test_reject_deactivation_occupied(self):
        self.seat()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE physical_tables SET active=0 WHERE venue_id='v'")

    def test_reject_guest_increase(self):
        self.seat()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE seating_sessions SET guest_count=5 WHERE session_id='s'")

    def test_closed_history_allows_reduction(self):
        self.seat(3,"closed")
        self.db.execute("UPDATE physical_tables SET capacity_seats=2 WHERE venue_id='v'")

    def test_reject_reactivation_overcapacity(self):
        self.seat(3,"closed")
        self.db.execute("UPDATE physical_tables SET capacity_seats=2 WHERE venue_id='v'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE seating_sessions SET state='active' WHERE session_id='s'")

    def test_venue_isolation(self):
        self.db.execute("INSERT INTO physical_tables VALUES ('w','t',1,1)")
        self.db.execute("INSERT INTO seating_sessions VALUES ('w','s','t',1,'active')")
        self.seat(4)

    def test_duplicate_active_session(self):
        self.seat()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO seating_sessions VALUES ('v','s2','t',2,'active')")

if __name__ == "__main__":
    unittest.main()
