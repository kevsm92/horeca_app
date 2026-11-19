"""Synthetic replay-integrity regression for the offline finalized-order bridge."""
import sqlite3
import unittest
from order_stock_bridge import consume_finalized_order
from order_stock_event import initialize
from prototypes.stock_event import Deduction

class OrderStockReplayTests(unittest.TestCase):
    def test_changed_finalized_snapshot_cannot_deduct_again(self):
        db = sqlite3.connect(':memory:')
        try:
            initialize(db)
            order = {'id': 'order-1', 'venue_id': 'venue-a', 'status': 'finalized', 'lines': (('dish-1', 2),)}
            recipes = {'dish-1': (Deduction('flour', 125),)}
            self.assertTrue(consume_finalized_order(db, venue_id='venue-a', order=order, recipes=recipes))
            with self.assertRaisesRegex(ValueError, 'different payload'):
                consume_finalized_order(db, venue_id='venue-a', order={**order, 'lines': (('dish-1', 3),)}, recipes=recipes)
            self.assertEqual(db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT ingredient_id, delta_milliunits FROM order_stock_ledger').fetchall(), [('flour', -250)])
        finally:
            db.close()

if __name__ == '__main__':
    unittest.main()
