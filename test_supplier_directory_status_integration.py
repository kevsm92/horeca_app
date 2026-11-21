"""Synthetic integration regression for supplier activation and quote visibility."""
import sqlite3
import unittest

from supplier_directory import initialize, add_supplier, add_sku, list_skus
from supplier_status import set_supplier_active


class SupplierStatusDirectoryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        for venue in ('venue-a', 'venue-b'):
            add_supplier(self.db, venue, 'shared', 'Fictional Supplier')
            add_sku(self.db, venue, 'shared', 'SKU-1', 'flour', 'kg', 1, 250, 2)

    def tearDown(self):
        self.db.close()

    def test_deactivation_hides_only_own_venue_quotes(self):
        self.assertEqual(len(list_skus(self.db, 'venue-a', 'flour')), 1)
        self.assertTrue(set_supplier_active(self.db, venue_id='venue-a', supplier_id='shared', active=False))
        self.assertEqual(list_skus(self.db, 'venue-a', 'flour'), [])
        self.assertEqual(len(list_skus(self.db, 'venue-b', 'flour')), 1)

    def test_reactivation_restores_original_quote_without_rewriting_history(self):
        original = list_skus(self.db, 'venue-a', 'flour')
        set_supplier_active(self.db, venue_id='venue-a', supplier_id='shared', active=False)
        retained = self.db.execute('SELECT sku, price_cents FROM supplier_sku WHERE venue_id=?', ('venue-a',)).fetchall()
        self.assertEqual(retained, [('SKU-1', 250)])
        set_supplier_active(self.db, venue_id='venue-a', supplier_id='shared', active=True)
        self.assertEqual(list_skus(self.db, 'venue-a', 'flour'), original)

    def test_inactive_supplier_cannot_bypass_filter_via_other_ingredient(self):
        add_sku(self.db, 'venue-a', 'shared', 'SKU-2', 'milk', 'l', 1, 180, 1)
        set_supplier_active(self.db, venue_id='venue-a', supplier_id='shared', active=False)
        self.assertEqual(list_skus(self.db, 'venue-a', 'milk'), [])
        self.assertEqual(list_skus(self.db, 'venue-a', 'flour'), [])


if __name__ == '__main__':
    unittest.main()
