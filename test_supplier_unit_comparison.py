import sqlite3
import unittest
from fractions import Fraction
from supplier_directory import initialize
from supplier_unit_comparison import compare_supplier_unit_prices

class SupplierUnitComparisonTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        self.db.executemany('INSERT INTO supplier(venue_id,supplier_id,display_name,active) VALUES (?,?,?,?)', [
            ('a','s1','Synthetic A',1),('a','s2','Synthetic B',1),
            ('a','inactive','Inactive',0),('b','s1','Other tenant',1)])

    def tearDown(self):
        self.db.close()

    def offer(self, venue, supplier, sku, unit, qty, price, lead=2):
        self.db.execute('''INSERT INTO supplier_sku
            (venue_id,supplier_id,sku,ingredient_id,unit,pack_quantity,price_cents,lead_days)
            VALUES (?,?,?,?,?,?,?,?)''',
                        (venue,supplier,sku,'flour',unit,qty,price,lead))

    def test_exact_normalization_and_tie_break(self):
        self.offer('a','s1','kg','kg',2,1000,3)
        self.offer('a','s2','g','g',500,250,1)
        mass = compare_supplier_unit_prices(self.db,'a','flour')['mass']
        self.assertEqual([o['sku'] for o in mass], ['g','kg'])
        self.assertEqual([o['unit_price_cents'] for o in mass], [Fraction(1,2)] * 2)

    def test_dimensions_never_compared(self):
        self.offer('a','s1','water','l',1,100)
        self.offer('a','s2','piece','each',1,1)
        result = compare_supplier_unit_prices(self.db,'a','flour')
        self.assertEqual(set(result), {'volume','count'})
        self.assertEqual(result['volume'][0]['base_unit'], 'ml')

    def test_tenant_inactive_and_ingredient_isolation(self):
        self.offer('a','s1','a','kg',1,100)
        self.offer('a','inactive','hidden','kg',1,1)
        self.offer('b','s1','foreign','kg',1,1)
        self.assertEqual([o['sku'] for o in compare_supplier_unit_prices(self.db,'a','flour')['mass']], ['a'])
        self.assertEqual(compare_supplier_unit_prices(self.db,'a','milk'), {})

    def test_scope_and_corrupt_rows_fail_closed(self):
        for venue, ingredient in [('', 'flour'), ('a', ''), (None, 'flour')]:
            with self.assertRaises(ValueError):
                compare_supplier_unit_prices(self.db, venue, ingredient)
        self.offer('a','s1','bad','kg',0,100)
        with self.assertRaises(ValueError):
            compare_supplier_unit_prices(self.db,'a','flour')

    def test_read_only(self):
        self.offer('a','s1','one','each',3,100)
        before = self.db.total_changes
        self.assertEqual(compare_supplier_unit_prices(self.db,'a','flour')['count'][0]['unit_price_cents'], Fraction(100,3))
        self.assertEqual(self.db.total_changes, before)

if __name__ == '__main__':
    unittest.main()
