import sqlite3
import tempfile
import unittest
from pathlib import Path
from menu_catalog import connect, list_items, seed_synthetic

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / 'catalog.sqlite')
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
    def test_empty_catalog(self):
        self.assertEqual(list_items(self.db, authorized_venue_id='a'), [])
    def test_seed_idempotent(self):
        seed_synthetic(self.db, venue_id='a')
        seed_synthetic(self.db, venue_id='a')
        self.assertEqual(len(list_items(self.db, authorized_venue_id='a')), 2)
    def test_tenant_isolation(self):
        seed_synthetic(self.db, venue_id='a')
        self.assertEqual(list_items(self.db, authorized_venue_id='b'), [])
    def test_kind_filter(self):
        seed_synthetic(self.db, venue_id='a')
        self.assertEqual([x['kind'] for x in list_items(self.db, authorized_venue_id='a', kind='drink')], ['drink'])
    def test_reject_invalid_scope(self):
        for venue in ('', '  ', None):
            with self.assertRaises(ValueError): list_items(self.db, authorized_venue_id=venue)
    def test_reject_invalid_kind(self):
        with self.assertRaises(ValueError): list_items(self.db, authorized_venue_id='a', kind='dessert')
    def test_constraints(self):
        for kind, price, available in [('bad',10,1),('food',-1,1),('food',2.5,1),('food',100,2)]:
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute('INSERT INTO menu_items (venue_id,item_id,kind,name,price_cents,available) VALUES (?,?,?,?,?,?)',('a','x',kind,'Dish',price,available))
    def test_same_id_across_venues(self):
        seed_synthetic(self.db, venue_id='a')
        seed_synthetic(self.db, venue_id='b')
        self.assertEqual(len(list_items(self.db, authorized_venue_id='b')), 2)
    def test_no_overwrite(self):
        seed_synthetic(self.db, venue_id='a')
        self.db.execute("UPDATE menu_items SET price_cents=999 WHERE venue_id='a' AND item_id='demo-food-1'")
        seed_synthetic(self.db, venue_id='a')
        self.assertEqual(next(x for x in list_items(self.db, authorized_venue_id='a') if x['item_id']=='demo-food-1')['price_cents'],999)

if __name__ == '__main__': unittest.main()
