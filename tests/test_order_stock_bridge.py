"""Synthetic-only regression tests for finalized-order stock adapter."""
import sqlite3
import unittest
from order_stock_event import initialize
from order_stock_bridge import consume_finalized_order
from prototypes.stock_event import Deduction

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        self.order = {'id': 'order-42', 'venue_id': 'venue-a', 'status': 'finalized', 'lines': (('latte', 2),)}
        self.recipes = {'latte': (Deduction('beans', 18), Deduction('milk', 200))}
    def tearDown(self):
        self.db.close()
    def run_bridge(self, **kw):
        return consume_finalized_order(self.db, venue_id=kw.get('venue_id', 'venue-a'),
                                       order=kw.get('order', self.order), recipes=self.recipes)
    def test_finalized_writes_aggregated_ledger(self):
        self.assertTrue(self.run_bridge())
        self.assertEqual(self.db.execute('SELECT ingredient_id,delta_milliunits FROM order_stock_ledger ORDER BY ingredient_id').fetchall(),
                         [('beans', -36), ('milk', -400)])
    def test_retry_no_double_deduction(self):
        self.assertTrue(self.run_bridge())
        self.assertFalse(self.run_bridge())
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_ledger').fetchone()[0], 2)
    def test_reject_wrong_venue(self):
        with self.assertRaises(ValueError):
            self.run_bridge(venue_id='venue-b')
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 0)
    def test_reject_unfinalized_and_voided(self):
        for status in ('new', 'preparing', 'voided', 'paid', None):
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.run_bridge(order={**self.order, 'status': status})
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 0)
    def test_conflicting_finalized_retry_rejected(self):
        self.run_bridge()
        with self.assertRaises(ValueError):
            self.run_bridge(order={**self.order, 'lines': (('latte', 3),)})
        self.assertEqual(self.db.execute('SELECT sum(delta_milliunits) FROM order_stock_ledger').fetchone()[0], -436)
    def test_missing_recipe_fails_closed(self):
        with self.assertRaises(ValueError):
            consume_finalized_order(self.db, venue_id='venue-a', order=self.order, recipes={})
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 0)

if __name__ == '__main__':
    unittest.main()
