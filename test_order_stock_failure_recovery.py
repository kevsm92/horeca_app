"""Synthetic rollback/retry regression for offline order-stock consumption."""
import sqlite3
import unittest

from order_stock_event import initialize, record_order_consumption


class OrderStockFailureRecoveryTests(unittest.TestCase):
    def test_partial_ledger_failure_can_retry_exact_event_once(self):
        db = sqlite3.connect(':memory:')
        try:
            initialize(db)
            args = dict(venue_id='venue-a', event_id='evt-1', order_id='ord-1',
                        ingredients={'apple': 5, 'zucchini': 8})
            db.execute('''CREATE TRIGGER fail_second_ingredient
                BEFORE INSERT ON order_stock_ledger
                WHEN NEW.ingredient_id = 'zucchini'
                BEGIN SELECT RAISE(ABORT, 'synthetic downstream failure'); END''')
            with self.assertRaises(sqlite3.IntegrityError):
                record_order_consumption(db, **args)
            self.assertFalse(db.in_transaction)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_events').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_ledger').fetchone()[0], 0)
            db.execute('DROP TRIGGER fail_second_ingredient')
            self.assertTrue(record_order_consumption(db, **args))
            self.assertFalse(record_order_consumption(db, **args))
            self.assertEqual(db.execute('SELECT ingredient_id, delta_milliunits FROM order_stock_ledger ORDER BY ingredient_id').fetchall(),
                             [('apple', -5), ('zucchini', -8)])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_events').fetchone()[0], 1)
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
