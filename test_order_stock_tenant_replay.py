"""Synthetic isolation regression for the offline order-to-stock event adapter."""
import sqlite3
import unittest

from order_stock_event import initialize, record_order_consumption


class TenantReplayIsolationTests(unittest.TestCase):
    def test_same_order_and_event_keys_are_isolated_per_venue(self):
        db = sqlite3.connect(':memory:')
        try:
            initialize(db)
            args = dict(event_id='order:shared:stock-deduct:v1', order_id='shared')
            self.assertTrue(record_order_consumption(db, venue_id='venue-a', ingredients={'flour': 100}, **args))
            self.assertTrue(record_order_consumption(db, venue_id='venue-b', ingredients={'flour': 250}, **args))
            self.assertFalse(record_order_consumption(db, venue_id='venue-a', ingredients={'flour': 100}, **args))
            self.assertFalse(record_order_consumption(db, venue_id='venue-b', ingredients={'flour': 250}, **args))
            with self.assertRaisesRegex(ValueError, 'different payload'):
                record_order_consumption(db, venue_id='venue-a', ingredients={'flour': 250}, **args)
            self.assertEqual(db.execute('SELECT venue_id, delta_milliunits FROM order_stock_ledger ORDER BY venue_id').fetchall(), [('venue-a', -100), ('venue-b', -250)])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_events').fetchone()[0], 2)
            self.assertFalse(db.in_transaction)
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
