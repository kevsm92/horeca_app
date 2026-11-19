import sqlite3
import unittest
from menu_catalog import initialize, add_item, list_items


class MenuCatalogTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        add_item(self.db, venue_id='fictional-a', item_id='f1', kind='food',
                 name='Synthetic soup', price_cents=850)
        add_item(self.db, venue_id='fictional-b', item_id='d1', kind='drink',
                 name='Synthetic tea', price_cents=320, available=False)

    def tearDown(self):
        self.db.close()

    def test_tenant_isolation_and_contract(self):
        self.assertEqual(list_items(self.db, authorized_venue_id='fictional-a'),
                         [{'id': 'f1', 'type': 'food', 'name': 'Synthetic soup',
                           'price_cents': 850, 'currency': 'EUR', 'available': True}])
        self.assertEqual(list_items(self.db, authorized_venue_id='fictional-b')[0]['available'], False)
        self.assertEqual(list_items(self.db, authorized_venue_id='fictional-c'), [])

    def test_missing_authorized_venue_rejected(self):
        with self.assertRaises(ValueError):
            list_items(self.db, authorized_venue_id='')

    def test_duplicate_and_invalid_price_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            add_item(self.db, venue_id='fictional-a', item_id='f1', kind='food',
                     name='Duplicate', price_cents=1)
        for price in (-1, 2.5, True):
            with self.assertRaises((ValueError, sqlite3.IntegrityError)):
                add_item(self.db, venue_id='fictional-a', item_id='x', kind='food',
                         name='Invalid', price_cents=price)

    def test_invalid_type_and_availability_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            add_item(self.db, venue_id='fictional-a', item_id='x', kind='other',
                     name='Invalid', price_cents=100)
        with self.assertRaises(ValueError):
            add_item(self.db, venue_id='fictional-a', item_id='x', kind='food',
                     name='Invalid', price_cents=100, available=1)


if __name__ == '__main__':
    unittest.main()
