"""Synthetic regression: distinct event IDs cannot double-consume an order."""
import sqlite3
import unittest
from order_stock_event import initialize, record_order_consumption


class OrderKeyReplayTests(unittest.TestCase):
    def test_same_order_new_event_rejected_but_other_venue_allowed(self):
        db = sqlite3.connect(':memory:')
        try:
            initialize(db)
            base = dict(venue_id='fictional-a', event_id='evt-a', order_id='order-1', ingredients={'milk': 120})
            self.assertTrue(record_order_consumption(db, **base))
            with self.assertRaisesRegex(ValueError, 'Order already consumed'):
                record_order_consumption(db, **{**base, 'event_id': 'evt-b'})
            self.assertFalse(db.in_transaction)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_events WHERE venue_id=?', ('fictional-a',)).fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT SUM(delta_milliunits) FROM order_stock_ledger WHERE venue_id=?', ('fictional-a',)).fetchone()[0], -120)
            self.assertTrue(record_order_consumption(db, **{**base, 'venue_id': 'fictional-b', 'event_id': 'evt-b'}))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_events').fetchone()[0], 2)
            self.assertEqual(db.execute('SELECT SUM(delta_milliunits) FROM order_stock_ledger').fetchone()[0], -240)
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
