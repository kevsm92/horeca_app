"""Synthetic failure-injection regression for atomic order-stock persistence."""
import sqlite3
import unittest

from order_stock_event import initialize, record_order_consumption


class StockAtomicRollbackTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        self.event = dict(venue_id='fictional-venue', event_id='order:42:stock-deduct:v1',
                          order_id='42', ingredients={'beans': 18, 'milk': 200})

    def tearDown(self):
        self.db.close()

    def test_failed_second_ingredient_rolls_back_event_and_first_ingredient(self):
        self.db.execute("""CREATE TRIGGER fail_milk BEFORE INSERT ON order_stock_ledger
            WHEN NEW.ingredient_id='milk' BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            record_order_consumption(self.db, **self.event)
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_ledger').fetchone()[0], 0)
        self.assertFalse(self.db.in_transaction)

        self.db.execute('DROP TRIGGER fail_milk')
        self.assertTrue(record_order_consumption(self.db, **self.event))
        self.assertEqual(self.db.execute('SELECT ingredient_id,delta_milliunits FROM order_stock_ledger ORDER BY ingredient_id').fetchall(),
                         [('beans', -18), ('milk', -200)])
        self.assertFalse(record_order_consumption(self.db, **self.event))

    def test_conflicting_retry_preserves_existing_event_and_ledger(self):
        self.assertTrue(record_order_consumption(self.db, **self.event))
        with self.assertRaises(ValueError):
            record_order_consumption(self.db, **{**self.event, 'ingredients': {'beans': 19}})
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT sum(delta_milliunits) FROM order_stock_ledger').fetchone()[0], -218)
        self.assertFalse(self.db.in_transaction)


if __name__ == '__main__':
    unittest.main()
