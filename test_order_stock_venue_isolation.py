"""Cross-venue synthetic stock event isolation and replay regression."""
import sqlite3
import unittest
from order_stock_event import initialize, record_order_consumption


class OrderStockVenueIsolationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)

    def tearDown(self):
        self.db.close()

    def consume(self, venue, ingredients):
        return record_order_consumption(self.db, venue_id=venue,
            event_id='order:shared:stock-deduct:v1', order_id='shared',
            ingredients=ingredients)

    def test_same_event_key_is_independent_across_venues(self):
        self.assertTrue(self.consume('venue-a', {'milk': 100}))
        self.assertTrue(self.consume('venue-b', {'milk': 250}))
        self.assertEqual(self.db.execute('SELECT venue_id,delta_milliunits FROM order_stock_ledger ORDER BY venue_id').fetchall(),
                         [('venue-a', -100), ('venue-b', -250)])
        self.assertFalse(self.consume('venue-a', {'milk': 100}))
        self.assertFalse(self.consume('venue-b', {'milk': 250}))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM order_stock_ledger').fetchone()[0], 2)

    def test_conflicting_replay_cannot_mutate_other_venue(self):
        self.consume('venue-a', {'milk': 100})
        self.consume('venue-b', {'milk': 250})
        with self.assertRaisesRegex(ValueError, 'different payload'):
            self.consume('venue-a', {'milk': 999})
        self.assertEqual(self.db.execute('SELECT venue_id,delta_milliunits FROM order_stock_ledger ORDER BY venue_id').fetchall(),
                         [('venue-a', -100), ('venue-b', -250)])
        self.assertFalse(self.db.in_transaction)


if __name__ == '__main__':
    unittest.main()
