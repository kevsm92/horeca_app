import sqlite3
import unittest
from supplier_directory import initialize, add_supplier, add_sku
from supplier_sku_lookup import resolve_supplier_sku

class SupplierSkuLookupTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        for venue, price in [('a', 1200), ('b', 9900)]:
            add_supplier(self.db, venue, 'shared', 'Fictional Supplier')
            add_sku(self.db, venue, 'shared', 'S-1', 'flour', 'kg', 10, price, 3)

    def tearDown(self):
        self.db.close()

    def test_same_sku_is_venue_bound(self):
        a = resolve_supplier_sku(self.db, venue_id='a', supplier_id='shared', sku='S-1')
        b = resolve_supplier_sku(self.db, venue_id='b', supplier_id='shared', sku='S-1')
        self.assertEqual(a['price_cents'], 1200)
        self.assertEqual(b['price_cents'], 9900)
        self.assertEqual(a['currency'], 'EUR')
        self.assertEqual(a['ingredient_id'], 'flour')

    def test_missing_and_inactive_fail_closed(self):
        self.assertIsNone(resolve_supplier_sku(self.db, venue_id='a', supplier_id='shared', sku='missing'))
        self.db.execute('UPDATE supplier SET active=0 WHERE venue_id=?', ('a',))
        self.assertIsNone(resolve_supplier_sku(self.db, venue_id='a', supplier_id='shared', sku='S-1'))
        self.assertIsNotNone(resolve_supplier_sku(self.db, venue_id='b', supplier_id='shared', sku='S-1'))

    def test_invalid_selectors_rejected(self):
        for kw in ({'venue_id':' ', 'supplier_id':'shared', 'sku':'S-1'},
                   {'venue_id':'a', 'supplier_id':None, 'sku':'S-1'},
                   {'venue_id':'a', 'supplier_id':'shared', 'sku':1}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                resolve_supplier_sku(self.db, **kw)

if __name__ == '__main__':
    unittest.main()
