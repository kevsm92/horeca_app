"""Regression: shared BOM ingredients aggregate once per finalized order.

Run: python -m unittest -v test_order_stock_shared_ingredient_aggregation.py
Synthetic-only, offline; does not validate recipe approval or real stock availability.
"""
import sqlite3
import unittest

from order_stock_bridge import consume_finalized_order
from order_stock_event import initialize
from prototypes.stock_event import Deduction


class SharedIngredientAggregationTests(unittest.TestCase):
    def test_repeated_lines_and_shared_recipe_ingredient_write_one_deduction(self):
        db = sqlite3.connect(':memory:')
        try:
            initialize(db)
            recipes = {
                'dish': (Deduction('flour', 120), Deduction('salt', 3)),
                'side': (Deduction('flour', 40), Deduction('oil', 15)),
            }
            order = {'id': 'order-shared', 'venue_id': 'venue-a', 'status': 'finalized',
                     'lines': (('dish', 2), ('side', 1), ('dish', 1))}
            self.assertTrue(consume_finalized_order(db, venue_id='venue-a', order=order, recipes=recipes))
            self.assertEqual(db.execute('SELECT ingredient_id,delta_milliunits FROM order_stock_ledger ORDER BY ingredient_id').fetchall(),
                             [('flour', -400), ('oil', -15), ('salt', -9)])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_events').fetchone()[0], 1)
            # Reordering equivalent finalized lines must not create a second stock event.
            reordered = {**order, 'lines': (('side', 1), ('dish', 1), ('dish', 2))}
            self.assertFalse(consume_finalized_order(db, venue_id='venue-a', order=reordered, recipes=recipes))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_ledger').fetchone()[0], 3)
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
