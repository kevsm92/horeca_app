"""Offline SQLite reference: atomic venue-scoped seat-capacity resize.

No authentication or production migration. Caller must authorize venue and table.
Visual geometry is intentionally not stored here; see table_resize_preflight.
"""
import sqlite3
import unittest


def install(db):
    db.executescript("""
    CREATE TABLE physical_tables (
      venue_id TEXT NOT NULL, table_id TEXT NOT NULL,
      capacity_seats INTEGER NOT NULL CHECK(capacity_seats BETWEEN 1 AND 100),
      inventory_seats INTEGER NOT NULL CHECK(inventory_seats BETWEEN 1 AND 100),
      revision INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY (venue_id, table_id),
      CHECK(capacity_seats <= inventory_seats));
    CREATE TABLE seating_sessions (
      venue_id TEXT NOT NULL, session_id TEXT NOT NULL, table_id TEXT NOT NULL,
      guest_count INTEGER NOT NULL CHECK(guest_count >= 1),
      state TEXT NOT NULL CHECK(state IN ('active','closed')),
      PRIMARY KEY (venue_id, session_id),
      FOREIGN KEY (venue_id, table_id) REFERENCES physical_tables(venue_id, table_id));
    CREATE UNIQUE INDEX one_active_per_table ON seating_sessions(venue_id,table_id)
      WHERE state='active';
    CREATE TRIGGER resize_occupancy_guard BEFORE UPDATE OF capacity_seats ON physical_tables
    BEGIN
      SELECT RAISE(ABORT,'occupied beyond proposed seats') WHERE EXISTS (
        SELECT 1 FROM seating_sessions s WHERE s.venue_id=NEW.venue_id
        AND s.table_id=NEW.table_id AND s.state='active'
        AND s.guest_count>NEW.capacity_seats);
    END;
    """)


def resize(db, venue_id, table_id, expected_revision, requested_seats):
    """Commit a revision-checked capacity change or rollback without side effects."""
    if not all(isinstance(v, str) and v for v in (venue_id, table_id)):
        raise ValueError('venue and table identifiers required')
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError('invalid expected revision')
    if type(requested_seats) is not int or not 1 <= requested_seats <= 100:
        raise ValueError('invalid requested seats')
    db.execute('BEGIN IMMEDIATE')
    try:
        cursor = db.execute("""UPDATE physical_tables
          SET capacity_seats=?, revision=revision+1
          WHERE venue_id=? AND table_id=? AND revision=?
            AND inventory_seats>=?""",
            (requested_seats, venue_id, table_id, expected_revision, requested_seats))
        if cursor.rowcount != 1:
            raise ValueError('stale revision, wrong scope or insufficient inventory')
        db.commit()
    except BaseException:
        db.rollback()
        raise
    return expected_revision + 1


class AtomicResizeTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON')
        install(self.db)
        self.db.execute("INSERT INTO physical_tables VALUES ('v1','t1',4,6,0)")
        self.db.execute("INSERT INTO physical_tables VALUES ('v2','t1',4,4,0)")
        self.db.execute("INSERT INTO seating_sessions VALUES ('v1','s1','t1',3,'active')")

    def tearDown(self):
        self.db.close()

    def state(self, venue='v1'):
        return self.db.execute('SELECT capacity_seats,revision FROM physical_tables WHERE venue_id=?', (venue,)).fetchone()

    def test_success_revision(self):
        self.assertEqual(resize(self.db,'v1','t1',0,3),1)
        self.assertEqual(self.state(),(3,1))

    def test_below_active_guests_rolls_back(self):
        with self.assertRaises(sqlite3.IntegrityError):
            resize(self.db,'v1','t1',0,2)
        self.assertEqual(self.state(),(4,0))

    def test_inventory_limit_rolls_back(self):
        with self.assertRaises(ValueError):
            resize(self.db,'v1','t1',0,7)
        self.assertEqual(self.state(),(4,0))

    def test_stale_revision_rejected(self):
        resize(self.db,'v1','t1',0,5)
        with self.assertRaises(ValueError):
            resize(self.db,'v1','t1',0,6)
        self.assertEqual(self.state(),(5,1))

    def test_cross_venue_isolation(self):
        with self.assertRaises(ValueError):
            resize(self.db,'v3','t1',0,3)
        self.assertEqual(self.state('v2'),(4,0))

    def test_invalid_type_rejected(self):
        for value in (True,2.5,'3',0,101):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resize(self.db,'v1','t1',0,value)
        self.assertEqual(self.state(),(4,0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
