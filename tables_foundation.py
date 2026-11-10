"""Venue-scoped table inventory and atomic seating (SQLite prototype; synthetic data only)."""
import sqlite3

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS physical_tables (
 venue_id TEXT NOT NULL, table_id TEXT NOT NULL,
 capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 100),
 PRIMARY KEY(venue_id, table_id)
);
CREATE TABLE IF NOT EXISTS seating_sessions (
 session_id TEXT PRIMARY KEY, venue_id TEXT NOT NULL, table_id TEXT NOT NULL,
 guest_count INTEGER NOT NULL CHECK(guest_count > 0),
 status TEXT NOT NULL CHECK(status IN ('active','closed')),
 FOREIGN KEY(venue_id, table_id) REFERENCES physical_tables(venue_id, table_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_session_per_table
 ON seating_sessions(venue_id, table_id) WHERE status='active';
CREATE TRIGGER IF NOT EXISTS enforce_capacity_on_insert
 BEFORE INSERT ON seating_sessions WHEN NEW.status='active'
 BEGIN SELECT RAISE(ABORT, 'capacity exceeded') WHERE
 NEW.guest_count > (SELECT capacity FROM physical_tables
 WHERE venue_id=NEW.venue_id AND table_id=NEW.table_id); END;
CREATE TRIGGER IF NOT EXISTS enforce_capacity_on_update
 BEFORE UPDATE OF guest_count,status,venue_id,table_id ON seating_sessions
 WHEN NEW.status='active'
 BEGIN SELECT RAISE(ABORT, 'capacity exceeded') WHERE
 NEW.guest_count > (SELECT capacity FROM physical_tables
 WHERE venue_id=NEW.venue_id AND table_id=NEW.table_id); END;
CREATE TRIGGER IF NOT EXISTS prevent_capacity_below_active_guests
 BEFORE UPDATE OF capacity ON physical_tables
 BEGIN SELECT RAISE(ABORT, 'active guests exceed capacity') WHERE
 NEW.capacity < COALESCE((SELECT guest_count FROM seating_sessions
 WHERE venue_id=OLD.venue_id AND table_id=OLD.table_id AND status='active'),0); END;
"""

def connect(path=":memory:"):
    db = sqlite3.connect(path, isolation_level=None, timeout=5)
    db.executescript(SCHEMA)
    return db

def seat(db, session_id, venue_id, table_id, guests):
    """Atomic seating; DB constraints reject double seating, foreign tables and overcapacity."""
    with db:
        db.execute("INSERT INTO seating_sessions VALUES (?,?,?,?, 'active')",
                   (session_id, venue_id, table_id, guests))

def close(db, session_id, venue_id):
    with db:
        cursor = db.execute("UPDATE seating_sessions SET status='closed' "
                            "WHERE session_id=? AND venue_id=? AND status='active'",
                            (session_id, venue_id))
        if cursor.rowcount != 1:
            raise ValueError("active session not found in venue")
