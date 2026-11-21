import sqlite3
import unittest
from supplier_status import set_supplier_active

class SupplierStatusTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript('''CREATE TABLE supplier (
          venue_id TEXT NOT NULL, supplier_id TEXT NOT NULL,
          active INTEGER NOT NULL CHECK(active IN (0,1)),
          PRIMARY KEY(venue_id,supplier_id));
          INSERT INTO supplier VALUES ('a','shared',1),('b','shared',1);''')
    def tearDown(self): self.db.close()
    def status(self, venue):
        return self.db.execute('SELECT active FROM supplier WHERE venue_id=?', (venue,)).fetchone()[0]
    def test_venue_isolation(self):
        self.assertTrue(set_supplier_active(self.db,venue_id='a',supplier_id='shared',active=False))
        self.assertEqual((self.status('a'),self.status('b')),(0,1))
    def test_reactivation(self):
        set_supplier_active(self.db,venue_id='a',supplier_id='shared',active=False)
        self.assertTrue(set_supplier_active(self.db,venue_id='a',supplier_id='shared',active=True))
        self.assertEqual(self.status('a'),1)
    def test_unknown_supplier_no_mutation(self):
        self.assertFalse(set_supplier_active(self.db,venue_id='a',supplier_id='missing',active=False))
        self.assertEqual(self.status('a'),1)
    def test_reject_invalid_values(self):
        for kwargs in [dict(venue_id='',supplier_id='shared',active=False),
                       dict(venue_id='a',supplier_id='',active=False),
                       dict(venue_id='a',supplier_id='shared',active=1)]:
            with self.assertRaises(ValueError): set_supplier_active(self.db,**kwargs)
        self.assertEqual(self.status('a'),1)

if __name__ == '__main__': unittest.main()
