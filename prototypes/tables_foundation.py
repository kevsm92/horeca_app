"""Offline synthetic tables foundation; no API or production persistence.

Run: python -m unittest discover -s prototypes -p 'tables_foundation.py'
"""
import sqlite3
import unittest


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS physical_tables (
    venue_id TEXT NOT NULL,
    table_id TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 30),
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
    PRIMARY KEY (venue_id, table_id)
);
CREATE TABLE IF NOT EXISTS seating_sessions (
    session_id TEXT PRIMARY KEY,
    venue_id TEXT NOT NULL,
    table_id TEXT NOT NULL,
    guests INTEGER NOT NULL CHECK(guests > 0),
    started_at TEXT NOT NULL,
    ended_at TEXT,
    FOREIGN KEY(venue_id, table_id) REFERENCES physical_tables(venue_id, table_id),
    CHECK(ended_at IS NULL OR ended_at >= started_at)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_session_per_table
ON seating_sessions(venue_id, table_id) WHERE ended_at IS NULL;
"""


class TablesStore:
    def __init__(self, connection):
        self.db = connection
        self.db.executescript(SCHEMA)

    def add_table(self, venue, table, capacity):
        with self.db:
            self.db.execute(
                "INSERT INTO physical_tables(venue_id,table_id,capacity) VALUES(?,?,?)",
                (venue, table, capacity),
            )

    def seat(self, session, venue, table, guests, started_at):
        # BEGIN IMMEDIATE serializes competing SQLite writers; the partial
        # unique index remains the authoritative double-seating guard.
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT capacity,active FROM physical_tables "
                "WHERE venue_id=? AND table_id=?", (venue, table)
            ).fetchone()
            if row is None or not row[1] or not isinstance(guests, int) or isinstance(guests, bool) or guests < 1 or guests > row[0]:
                raise ValueError("Unknown/inactive table or invalid guest count")
            self.db.execute(
                "INSERT INTO seating_sessions(session_id,venue_id,table_id,guests,started_at) "
                "VALUES(?,?,?,?,?)", (session, venue, table, guests, started_at)
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def close(self, session, venue, ended_at):
        with self.db:
            cursor = self.db.execute(
                "UPDATE seating_sessions SET ended_at=? "
                "WHERE session_id=? AND venue_id=? AND ended_at IS NULL "
                "AND started_at<=?", (ended_at, session, venue, ended_at)
            )
            if cursor.rowcount != 1:
                raise ValueError("No matching active seating session")

    def change_capacity(self, venue, table, capacity):
        with self.db:
            cursor = self.db.execute(
                "UPDATE physical_tables SET capacity=? "
                "WHERE venue_id=? AND table_id=? AND ? >= COALESCE(("
                "SELECT MAX(guests) FROM seating_sessions s "
                "WHERE s.venue_id=physical_tables.venue_id "
                "AND s.table_id=physical_tables.table_id AND s.ended_at IS NULL"
                "),0)", (capacity, venue, table, capacity)
            )
            if cursor.rowcount != 1:
                raise ValueError("Capacity below active occupancy or table not found")


class TablesFoundationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.store = TablesStore(self.db)
        self.store.add_table("venue-a", "T1", 4)
        self.store.add_table("venue-b", "T1", 2)

    def tearDown(self):
        self.db.close()

    def test_double_seating_and_reseat_after_close(self):
        self.store.seat("s1", "venue-a", "T1", 3, "2026-11-11T12:00:00+01:00")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.seat("s2", "venue-a", "T1", 1, "2026-11-11T12:01:00+01:00")
        self.store.close("s1", "venue-a", "2026-11-11T13:00:00+01:00")
        self.store.seat("s2", "venue-a", "T1", 1, "2026-11-11T13:01:00+01:00")

    def test_capacity_and_venue_isolation(self):
        for venue, count in [("venue-a", 5), ("venue-b", 3), ("venue-x", 1)]:
            with self.assertRaises(ValueError):
                self.store.seat("bad-"+venue, venue, "T1", count, "2026-11-11T12:00:00+01:00")
        self.store.seat("s1", "venue-a", "T1", 4, "2026-11-11T12:00:00+01:00")
        with self.assertRaises(ValueError):
            self.store.change_capacity("venue-a", "T1", 3)
        self.store.change_capacity("venue-a", "T1", 4)
        with self.assertRaises(ValueError):
            self.store.close("s1", "venue-b", "2026-11-11T13:00:00+01:00")

    def test_invalid_capacity_and_guests(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.add_table("venue-a", "T0", 0)
        for guests in (0, -1, True):
            with self.assertRaises(ValueError):
                self.store.seat("bad", "venue-a", "T1", guests, "2026-11-11T12:00:00+01:00")


if __name__ == "__main__":
    unittest.main()
