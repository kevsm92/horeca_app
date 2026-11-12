"""Synthetic, offline tests for venue-scoped occupancy projection."""
import sqlite3
import unittest
from tables_occupancy import occupancy_for_venue


class OccupancyTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript('''
            CREATE TABLE physical_tables(venue_id TEXT, table_id TEXT, capacity INTEGER,
                PRIMARY KEY(venue_id,table_id));
            CREATE TABLE seating_sessions(session_id TEXT PRIMARY KEY, venue_id TEXT,
                table_id TEXT, guest_count INTEGER, status TEXT);
            CREATE UNIQUE INDEX active_unique ON seating_sessions(venue_id,table_id)
                WHERE status='active';
        ''')
        self.db.executemany('INSERT INTO physical_tables VALUES (?,?,?)',
            [('a','T1',4),('a','T2',2),('b','T1',9)])
        self.db.executemany('INSERT INTO seating_sessions VALUES (?,?,?,?,?)',
            [('old','a','T1',3,'closed'),('new','a','T1',2,'active'),
             ('secret','b','T1',8,'active')])

    def tearDown(self):
        self.db.close()

    def test_occupied_and_available(self):
        self.assertEqual(occupancy_for_venue(self.db,'a'),
            [('T1',4,'occupied',2,'new'),('T2',2,'available',0,None)])

    def test_tenant_isolation(self):
        self.assertEqual(occupancy_for_venue(self.db,'b'),
            [('T1',9,'occupied',8,'secret')])
        self.assertEqual(occupancy_for_venue(self.db,'unknown'), [])

    def test_closed_session_does_not_block_table(self):
        self.db.execute("UPDATE seating_sessions SET status='closed' WHERE session_id='new'")
        self.assertEqual(occupancy_for_venue(self.db,'a')[0],
            ('T1',4,'available',0,None))

    def test_invalid_venue_rejected(self):
        for venue in ('', '  ', None, 42):
            with self.subTest(venue=venue), self.assertRaises(ValueError):
                occupancy_for_venue(self.db,venue)


    def test_orphan_active_session_fails_closed(self):
        self.db.execute("INSERT INTO seating_sessions VALUES ('orphan','a','MISSING',1,'active')")
        with self.assertRaisesRegex(ValueError, 'missing physical table'):
            occupancy_for_venue(self.db,'a')

    def test_overcapacity_fails_closed(self):
        self.db.execute("UPDATE seating_sessions SET guest_count=5 WHERE session_id='new'")
        with self.assertRaisesRegex(ValueError, 'guest count'):
            occupancy_for_venue(self.db,'a')

    def test_zero_guests_fails_closed(self):
        self.db.execute("UPDATE seating_sessions SET guest_count=0 WHERE session_id='new'")
        with self.assertRaisesRegex(ValueError, 'guest count'):
            occupancy_for_venue(self.db,'a')

    def test_invalid_capacity_fails_closed(self):
        self.db.execute("UPDATE physical_tables SET capacity=0 WHERE venue_id='a' AND table_id='T2'")
        with self.assertRaisesRegex(ValueError, 'capacity'):
            occupancy_for_venue(self.db,'a')

    def test_other_venue_corruption_does_not_leak(self):
        self.db.execute("UPDATE seating_sessions SET guest_count=99 WHERE session_id='secret'")
        self.assertEqual(len(occupancy_for_venue(self.db,'a')), 2)

    def test_duplicate_active_sessions_fails_closed_without_unique_index(self):
        self.db.execute('DROP INDEX active_unique')
        self.db.execute("INSERT INTO seating_sessions VALUES ('double','a','T1',1,'active')")
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            occupancy_for_venue(self.db,'a')

if __name__ == '__main__':
    unittest.main()
