"""Synthetic regression: invalid ingredient amounts never produce partial deductions."""
import sqlite3
import unittest
from order_stock_event import initialize, record_order_consumption


class InvalidOrderAtomicityTests(unittest.TestCase):
    def test_invalid_quantities_leave_no_events_or_ledger_entries(self):
        db = sqlite3.connect(':memory:')
        try:
            initialize(db)
            for invalid in (0, -1, True, 1.5, '12', 1_000_000_001):
                with self.subTest(invalid=invalid):
                    with self.assertRaisesRegex(ValueError, 'Invalid ingredient quantity'):
                        record_order_consumption(
                            db, venue_id='fictional-a', event_id='evt-1',
                            order_id='order-1', ingredients={'milk': 120, 'eggs': invalid})
                    self.assertFalse(db.in_transaction)
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_events').fetchone()[0], 0)
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_ledger').fetchone()[0], 0)
            self.assertTrue(record_order_consumption(
                db, venue_id='fictional-a', event_id='evt-1',
                order_id='order-1', ingredients={'milk': 120, 'eggs': 2}))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_ledger').fetchone()[0], 2)
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
