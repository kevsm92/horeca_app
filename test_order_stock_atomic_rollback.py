"""Synthetic fault-injection regression: an incomplete stock event never persists."""
import sqlite3
import unittest

from order_stock_event import initialize, record_order_consumption


class AtomicRollbackTests(unittest.TestCase):
    def test_second_ingredient_failure_rolls_back_event_and_first_deduction(self):
        db = sqlite3.connect(':memory:')
        try:
            initialize(db)
            db.execute("""CREATE TRIGGER reject_synthetic_salt BEFORE INSERT ON order_stock_ledger
                       WHEN NEW.ingredient_id = 'salt'
                       BEGIN SELECT RAISE(ABORT, 'synthetic ingredient failure'); END""")
            args = dict(venue_id='fictional-venue', event_id='evt-rollback-1',
                        order_id='order-rollback-1', ingredients={'flour': 125, 'salt': 15})
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'synthetic ingredient failure'):
                record_order_consumption(db, **args)
            self.assertFalse(db.in_transaction)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_events').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_ledger').fetchone()[0], 0)
            db.execute('DROP TRIGGER reject_synthetic_salt')
            self.assertTrue(record_order_consumption(db, **args))
            self.assertFalse(record_order_consumption(db, **args))
            self.assertEqual(db.execute('SELECT ingredient_id, delta_milliunits FROM order_stock_ledger ORDER BY ingredient_id').fetchall(), [('flour', -125), ('salt', -15)])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_events').fetchone()[0], 1)
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
