"""Synthetic fault injection: partial stock deduction must never commit."""
import sqlite3
import unittest
from order_stock_event import initialize, record_order_consumption


class OrderStockAtomicFailureTests(unittest.TestCase):
    def test_second_ingredient_failure_rolls_back_event_and_first_ledger_row(self):
        db = sqlite3.connect(':memory:')
        try:
            initialize(db)
            db.execute('''CREATE TRIGGER reject_second_ingredient
                BEFORE INSERT ON order_stock_ledger
                WHEN NEW.ingredient_id = 'z-blocked'
                BEGIN SELECT RAISE(ABORT, 'synthetic stock write failure'); END''')
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'synthetic stock write failure'):
                record_order_consumption(db, venue_id='venue-a', event_id='finalized:order-1',
                                         order_id='order-1', ingredients={'a-flour': 125, 'z-blocked': 25})
            self.assertFalse(db.in_transaction)
            self.assertEqual(db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM order_stock_ledger').fetchone()[0], 0)
            db.execute('DROP TRIGGER reject_second_ingredient')
            self.assertTrue(record_order_consumption(db, venue_id='venue-a', event_id='finalized:order-1',
                                                     order_id='order-1', ingredients={'a-flour': 125, 'z-blocked': 25}))
            self.assertEqual(db.execute('SELECT count(*) FROM order_stock_ledger').fetchone()[0], 2)
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
