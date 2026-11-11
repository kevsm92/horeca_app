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


if __name__ == '__main__':
    unittest.main()
