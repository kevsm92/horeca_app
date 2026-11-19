"""Synthetic regression: a venue/order may be consumed only once, regardless of event key."""
import sqlite3
import unittest

from order_stock_event import initialize, record_order_consumption


class OrderUniquenessTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)

    def tearDown(self):
        self.db.close()

    def consume(self, venue='venue-a', event='event-1'):
        return record_order_consumption(
            self.db, venue_id=venue, event_id=event, order_id='order-1',
            ingredients={'milk': 5})

    def test_distinct_event_cannot_deduct_same_order_twice(self):
        self.assertTrue(self.consume())
        with self.assertRaisesRegex(ValueError, 'already consumed'):
            self.consume(event='event-2')
        self.assertEqual(self.db.execute(
            'SELECT count(*) FROM order_stock_ledger').fetchone()[0], 1)
        self.assertFalse(self.db.in_transaction)

    def test_order_identity_is_venue_scoped(self):
        self.assertTrue(self.consume())
        self.assertTrue(self.consume(venue='venue-b', event='event-2'))

    def test_exact_retry_remains_noop(self):
        self.assertTrue(self.consume())
        self.assertFalse(self.consume())

    def test_database_constraint_rejects_bypass(self):
        self.consume()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO order_stock_events VALUES ('venue-a','event-2','order-1','{}')")


if __name__ == '__main__':
    unittest.main()
