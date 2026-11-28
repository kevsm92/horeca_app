import sqlite3
import unittest
from stock_recount_events import initialize, record_event, list_events

BASE = dict(event_id='e1',venue_id='v1',sku_id='s1',recount_id='r1',
            event_type='count_recorded',actor_id='fictional-a',
            ledger_revision=2,quantity_milli=5000,occurred_at='2026-11-20T22:00:00+01:00')

class RecountEventTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)

    def tearDown(self):
        self.db.close()

    def add(self, **changes):
        record_event(self.db, **(BASE | changes))

    def test_scoped_read(self):
        self.add()
        self.assertEqual(len(list_events(self.db,venue_id='v1',sku_id='s1',recount_id='r1')),1)
        self.assertEqual(list_events(self.db,venue_id='v2',sku_id='s1',recount_id='r1'),[])

    def test_duplicate_id(self):
        self.add()
        with self.assertRaises(sqlite3.IntegrityError): self.add()

    def test_duplicate_type(self):
        self.add()
        with self.assertRaises(sqlite3.IntegrityError): self.add(event_id='e2')

    def test_cross_scope(self):
        self.add()
        with self.assertRaises(ValueError):
            self.add(event_id='e2',venue_id='v2',event_type='recount_recorded')

    def test_immutable_update(self):
        self.add()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('UPDATE stock_recount_events SET quantity_milli=1')

    def test_immutable_delete(self):
        self.add()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('DELETE FROM stock_recount_events')

    def test_negative_quantity(self):
        with self.assertRaises(ValueError): self.add(quantity_milli=-1)

    def test_boolean_revision(self):
        with self.assertRaises(ValueError): self.add(ledger_revision=True)

    def test_naive_time(self):
        with self.assertRaises(ValueError): self.add(occurred_at='2026-11-20T22:00:00')

    def test_unknown_event(self):
        with self.assertRaises(ValueError): self.add(event_type='approved')

    def test_second_event(self):
        self.add()
        self.add(event_id='e2',event_type='recount_recorded')
        self.assertEqual(len(list_events(self.db,venue_id='v1',sku_id='s1',recount_id='r1')),2)

    def test_missing_venue(self):
        with self.assertRaises(ValueError): self.add(venue_id='')

if __name__ == '__main__':
    unittest.main()
