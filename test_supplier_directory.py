import sqlite3
import unittest
from supplier_directory import initialize, add_supplier, add_sku, list_skus

class SupplierDirectoryTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        initialize(self.db)
        add_supplier(self.db,'venue-a','vendor-1','Fictional Wholesale')
        add_supplier(self.db,'venue-b','vendor-1','Other Fictional Wholesale')

    def tearDown(self):
        self.db.close()

    def test_venue_isolation_with_shared_supplier_id(self):
        add_sku(self.db,'venue-a','vendor-1','SKU-1','flour','kg',10,2500,2)
        add_sku(self.db,'venue-b','vendor-1','SKU-1','flour','kg',10,9999,4)
        self.assertEqual(list_skus(self.db,'venue-a','flour')[0][5],2500)
        self.assertEqual(list_skus(self.db,'venue-b','flour')[0][5],9999)
        self.assertEqual(list_skus(self.db,'venue-a','milk'),[])

    def test_cross_venue_supplier_reference_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            add_sku(self.db,'venue-c','vendor-1','SKU-1','flour','kg',1,100,1)

    def test_invalid_prices_lead_times_and_units_rejected(self):
        for unit,qty,price,lead in [('kg',1,-1,2),('kg',0,100,2),('kg',1,100,366),('pallet',1,100,2)]:
            with self.subTest(unit=unit,qty=qty,price=price,lead=lead):
                with self.assertRaises(sqlite3.IntegrityError):
                    add_sku(self.db,'venue-a','vendor-1','SKU-1','flour',unit,qty,price,lead)
        with self.assertRaises(ValueError):
            add_sku(self.db,'venue-a','vendor-1','SKU-1','flour','kg',True,100,1)

    def test_inactive_supplier_hidden_and_no_external_ordering(self):
        add_sku(self.db,'venue-a','vendor-1','SKU-1','flour','kg',1,100,1)
        self.db.execute('UPDATE supplier SET active=0 WHERE venue_id=? AND supplier_id=?',('venue-a','vendor-1'))
        self.assertEqual(list_skus(self.db,'venue-a','flour'),[])

if __name__=='__main__':
    unittest.main()
