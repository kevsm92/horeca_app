"""Offline SQLite seating reference. Synthetic only; NOT integrated or authenticated.
Run: python -m unittest tests.test_tables_reference -v
"""
import sqlite3
import unittest

DDL = """
PRAGMA foreign_keys=ON;
CREATE TABLE physical_tables (
 id TEXT PRIMARY KEY, venue_id TEXT NOT NULL, label TEXT NOT NULL,
 physical_seats INTEGER NOT NULL CHECK(physical_seats BETWEEN 1 AND 100),
 enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
 UNIQUE(venue_id,id), UNIQUE(venue_id,label));
CREATE TABLE seating_sessions (
 id TEXT PRIMARY KEY, venue_id TEXT NOT NULL, table_id TEXT NOT NULL,
 guest_count INTEGER NOT NULL CHECK(guest_count>0),
 started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, ended_at TEXT,
 FOREIGN KEY(venue_id,table_id) REFERENCES physical_tables(venue_id,id),
 CHECK(ended_at IS NULL OR ended_at>=started_at));
CREATE UNIQUE INDEX one_active_session ON seating_sessions(venue_id,table_id)
 WHERE ended_at IS NULL;
"""

def seat(conn, venue, table, session, guests):
    """Requires an already authenticated, venue-authorized caller."""
    if type(guests) is not int or guests <= 0:
        raise ValueError("invalid guest count")
    with conn:
        row = conn.execute("SELECT physical_seats,enabled FROM physical_tables WHERE venue_id=? AND id=?",
                           (venue,table)).fetchone()
        if row is None:
            raise LookupError("table unavailable")
        if not row[1] or guests > row[0]:
            raise ValueError("disabled or over capacity")
        try:
            conn.execute("INSERT INTO seating_sessions(id,venue_id,table_id,guest_count) VALUES(?,?,?,?)",
                         (session,venue,table,guests))
        except sqlite3.IntegrityError as exc:
            raise ValueError("session conflict") from exc
    return session

def resize(conn, venue, table, capacity):
    if type(capacity) is not int or not 1 <= capacity <= 100:
        raise ValueError("invalid capacity")
    with conn:
        result = conn.execute("""UPDATE physical_tables SET physical_seats=?
          WHERE venue_id=? AND id=? AND NOT EXISTS (
            SELECT 1 FROM seating_sessions s
            WHERE s.venue_id=physical_tables.venue_id AND s.table_id=physical_tables.id
              AND s.ended_at IS NULL AND s.guest_count>?)""",
            (capacity,venue,table,capacity))
        if result.rowcount != 1:
            raise ValueError("missing table or occupied above capacity")

class Tests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.executescript(DDL)
        self.db.execute("INSERT INTO physical_tables(id,venue_id,label,physical_seats) VALUES('t','a','A1',4)")
    def tearDown(self):
        self.db.close()
    def test_double_seating(self):
        seat(self.db,"a","t","s1",3)
        with self.assertRaisesRegex(ValueError,"conflict"): seat(self.db,"a","t","s2",1)
        self.assertEqual(self.db.execute("SELECT count(*) FROM seating_sessions").fetchone()[0],1)
    def test_capacity(self):
        for count in (0,-1,5,True):
            with self.assertRaises(ValueError): seat(self.db,"a","t",str(count),count)
    def test_tenant(self):
        with self.assertRaises(LookupError): seat(self.db,"b","t","s",1)
    def test_resize(self):
        seat(self.db,"a","t","s",3)
        with self.assertRaises(ValueError): resize(self.db,"a","t",2)
        resize(self.db,"a","t",3)
    def test_reseat_after_end(self):
        seat(self.db,"a","t","s1",2)
        self.db.execute("UPDATE seating_sessions SET ended_at=started_at WHERE id='s1'")
        seat(self.db,"a","t","s2",2)
        self.assertEqual(self.db.execute("SELECT count(*) FROM seating_sessions").fetchone()[0],2)
    def test_disabled(self):
        self.db.execute("UPDATE physical_tables SET enabled=0 WHERE id='t'")
        with self.assertRaises(ValueError): seat(self.db,"a","t","s",1)
    def test_cross_venue_fk(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO seating_sessions(id,venue_id,table_id,guest_count) VALUES('s','b','t',1)")

if __name__ == "__main__":
    unittest.main()
