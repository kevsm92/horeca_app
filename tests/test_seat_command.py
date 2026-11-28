"""Synthetic regression tests for the offline Seat command."""
import sqlite3
import unittest
from pathlib import Path
from reference.tables.seat_command import seat, SeatRejected

ROOT = Path(__file__).resolve().parents[1]

class SeatCommandTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript((ROOT/"reference/tables/sqlite_seating_schema.sql").read_text()
                              + (ROOT/"reference/tables/sqlite_capacity_guards.sql").read_text())
        self.db.execute("INSERT INTO physical_tables VALUES ('v','t',4,1)")
        self.db.execute("INSERT INTO physical_tables VALUES ('other','t',1,1)")
        self.db.commit()
    def run_seat(self, **kw):
        seat(self.db, venue_id=kw.get("venue_id","v"), table_id=kw.get("table_id","t"),
             session_id=kw.get("session_id","s"), guests=kw.get("guests",2))
    def test_success(self):
        self.run_seat()
        self.assertEqual(self.db.execute("SELECT guest_count FROM seating_sessions").fetchone()[0],2)
    def test_capacity_rollback(self):
        with self.assertRaises(SeatRejected): self.run_seat(guests=5)
        self.assertEqual(self.db.execute("SELECT count(*) FROM seating_sessions").fetchone()[0],0)
    def test_duplicate_table(self):
        self.run_seat()
        with self.assertRaises(SeatRejected): self.run_seat(session_id="s2")
    def test_duplicate_session(self):
        self.run_seat()
        with self.assertRaises(SeatRejected): self.run_seat()
    def test_venue_scope(self):
        with self.assertRaises(SeatRejected): self.run_seat(venue_id="other",guests=2)
        with self.assertRaises(SeatRejected): self.run_seat(venue_id="missing")
    def test_inactive(self):
        self.db.execute("UPDATE physical_tables SET active=0 WHERE venue_id='v'")
        self.db.commit()
        with self.assertRaises(SeatRejected): self.run_seat()
    def test_invalid_counts(self):
        for n in (0,-1,True,1.5,"2"):
            with self.assertRaises(SeatRejected): self.run_seat(guests=n)
    def test_transaction_not_owned(self):
        self.db.execute("BEGIN")
        with self.assertRaises(SeatRejected): self.run_seat()
        self.assertTrue(self.db.in_transaction)
        self.db.rollback()

if __name__ == "__main__":
    unittest.main()
