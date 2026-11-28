import sqlite3
import unittest
from fractions import Fraction
from supplier_quotes import comparable_quotes


class SupplierQuotesTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript('''
            CREATE TABLE supplier(venue_id TEXT, supplier_id TEXT, display_name TEXT,
                                  active INTEGER, PRIMARY KEY(venue_id,supplier_id));
            CREATE TABLE supplier_sku(venue_id TEXT,supplier_id TEXT,sku TEXT,
                                      ingredient_id TEXT,unit TEXT,pack_quantity INTEGER,
                                      price_cents INTEGER,lead_days INTEGER);
        ''')
        self.db.executemany('INSERT INTO supplier VALUES(?,?,?,?)', [
            ('a','s1','Fictional A',1),('a','s2','Fictional B',1),
            ('a','s3','Inactive',0),('b','s1','Other venue',1)])

    def add(self, venue, supplier, sku, unit, qty, cents, lead=2):
        self.db.execute('INSERT INTO supplier_sku VALUES(?,?,?,?,?,?,?,?)',
                        (venue,supplier,sku,'flour',unit,qty,cents,lead))

    def tearDown(self):
        self.db.close()

    def test_normalizes_kg_and_g_exactly(self):
        self.add('a','s1','bulk','kg',2,500)
        self.add('a','s2','small','g',500,200)
        result = comparable_quotes(self.db,'a','flour')
        self.assertEqual([x[2] for x in result], ['bulk','small'])
        self.assertEqual(result[0][3], Fraction(1,4))

    def test_isolation_and_inactive_filter(self):
        self.add('a','s3','inactive','kg',1,1)
        self.add('b','s1','foreign','kg',1,1)
        self.assertEqual(comparable_quotes(self.db,'a','flour'), [])

    def test_mixed_dimensions_fail_closed(self):
        self.add('a','s1','mass','kg',1,100)
        self.add('a','s2','volume','l',1,100)
        with self.assertRaisesRegex(ValueError,'mixed unit'):
            comparable_quotes(self.db,'a','flour')

    def test_rejects_invalid_stored_data_and_empty_scope(self):
        self.add('a','s1','broken','kg',0,100)
        with self.assertRaises(ValueError):
            comparable_quotes(self.db,'a','flour')
        with self.assertRaises(ValueError):
            comparable_quotes(self.db,'','flour')

    def test_ties_use_lead_time_then_supplier(self):
        self.add('a','s1','slow','kg',1,100,5)
        self.add('a','s2','fast','g',1000,100,1)
        self.assertEqual(comparable_quotes(self.db,'a','flour')[0][2], 'fast')


if __name__ == '__main__':
    unittest.main()
