"""Synthetic regression tests for offline supplier lead-time preview."""
import sqlite3
import unittest
from supplier_directory import initialize, add_supplier, add_sku
from supplier_lead_time import eligible_supplier_skus


class SupplierLeadTimeTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        for venue in ('a', 'b'):
            for vendor in ('s1', 's2'):
                add_supplier(self.db, venue, vendor, 'Fictional ' + vendor)
        add_sku(self.db, 'a', 's1', 'fast', 'flour', 'kg', 1, 300, 0)
        add_sku(self.db, 'a', 's2', 'medium', 'flour', 'kg', 1, 200, 3)
        add_sku(self.db, 'a', 's1', 'slow', 'flour', 'kg', 1, 100, 7)
        add_sku(self.db, 'b', 's1', 'foreign', 'flour', 'kg', 1, 1, 0)
        add_sku(self.db, 'a', 's1', 'other', 'sugar', 'kg', 1, 1, 0)

    def tearDown(self):
        self.db.close()

    def test_horizon_is_inclusive_and_deterministic(self):
        self.assertEqual([r[2] for r in eligible_supplier_skus(self.db, 'a', 'flour', 3)],
                         ['fast', 'medium'])
        self.assertEqual([r[2] for r in eligible_supplier_skus(self.db, 'a', 'flour', 0)],
                         ['fast'])

    def test_venue_ingredient_and_inactive_supplier_isolation(self):
        self.db.execute("UPDATE supplier SET active=0 WHERE venue_id='a' AND supplier_id='s1'")
        self.assertEqual([r[2] for r in eligible_supplier_skus(self.db, 'a', 'flour', 365)],
                         ['medium'])
        self.assertEqual([r[2] for r in eligible_supplier_skus(self.db, 'b', 'flour', 365)],
                         ['foreign'])
        self.assertEqual(eligible_supplier_skus(self.db, 'a', 'unknown', 365), [])

    def test_invalid_scope_and_horizon_fail_closed(self):
        for value in (-1, 366, True, 1.5, '3', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                eligible_supplier_skus(self.db, 'a', 'flour', value)
        for venue, ingredient in (('', 'flour'), ('a', ' '), (None, 'flour')):
            with self.assertRaises(ValueError):
                eligible_supplier_skus(self.db, venue, ingredient, 3)


if __name__ == '__main__':
    unittest.main()
