"""Synthetic regression: changed BOM cannot silently rewrite finalized stock consumption."""
import sqlite3
import unittest

from order_stock_bridge import consume_finalized_order
from order_stock_event import initialize
from prototypes.stock_event import Deduction


class RecipeDriftReplayTests(unittest.TestCase):
    def test_recipe_revision_drift_rejected_without_ledger_mutation(self):
        db = sqlite3.connect(':memory:')
        try:
            initialize(db)
            order = {'id': 'ord-recipe-drift', 'venue_id': 'venue-a',
                     'status': 'finalized', 'lines': (('soup', 2),)}
            original = {'soup': (Deduction('carrot', 100), Deduction('salt', 2))}
            revised = {'soup': (Deduction('carrot', 150), Deduction('salt', 2))}
            self.assertTrue(consume_finalized_order(db, venue_id='venue-a', order=order, recipes=original))
            before = db.execute('SELECT ingredient_id,delta_milliunits FROM order_stock_ledger ORDER BY ingredient_id').fetchall()
            with self.assertRaisesRegex(ValueError, 'different payload'):
                consume_finalized_order(db, venue_id='venue-a', order=order, recipes=revised)
            self.assertEqual(db.execute('SELECT ingredient_id,delta_milliunits FROM order_stock_ledger ORDER BY ingredient_id').fetchall(), before)
            self.assertEqual(before, [('carrot', -200), ('salt', -4)])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_events').fetchone()[0], 1)
            self.assertFalse(db.in_transaction)
            self.assertFalse(consume_finalized_order(db, venue_id='venue-a', order=order, recipes=original))
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
