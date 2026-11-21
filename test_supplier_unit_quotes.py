"""Synthetic tests for normalized supplier quote preview."""
import sqlite3
import unittest
from supplier_directory import initialize, add_supplier, add_sku
from supplier_unit_quotes import compare_unit_quotes
from fractions import Fraction


class SupplierUnitQuotesTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        for venue in ('a', 'b'):
            for vendor in ('v1', 'v2'):
                add_supplier(self.db, venue, vendor, 'Fictional ' + vendor)
        add_sku(self.db, 'a', 'v1', 'small', 'flour', 'g', 500, 199, 3)
        add_sku(self.db, 'a', 'v2', 'large', 'flour', 'kg', 1, 399, 1)
        add_sku(self.db, 'a', 'v1', 'count', 'flour', 'each', 1, 1, 0)
        add_sku(self.db, 'b', 'v1', 'foreign', 'flour', 'kg', 1, 1, 0)

    def tearDown(self):
        self.db.close()

    def test_exact_normalized_order_and_incompatible_units(self):
        quotes = compare_unit_quotes(self.db, 'a', 'flour', 'kg')
        self.assertEqual([q[1] for q in quotes], ['small', 'large'])
        self.assertEqual(quotes[0][2], Fraction(398, 1))
        self.assertEqual(compare_unit_quotes(self.db, 'a', 'flour', 'each')[0][1], 'count')

    def test_venue_isolation_and_inactive_vendor(self):
        self.assertEqual([q[1] for q in compare_unit_quotes(self.db, 'b', 'flour', 'kg')], ['foreign'])
        self.db.execute("UPDATE supplier SET active=0 WHERE venue_id='a' AND supplier_id='v1'")
        self.assertEqual([q[1] for q in compare_unit_quotes(self.db, 'a', 'flour', 'kg')], ['large'])

    def test_invalid_scope_and_unit(self):
        for args in [('', 'flour', 'kg'), ('a', ' ', 'kg'), ('a', 'flour', 'pallet')]:
            with self.assertRaises(ValueError):
                compare_unit_quotes(self.db, *args)


if __name__ == '__main__':
    unittest.main()
