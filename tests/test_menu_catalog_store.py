"""Synthetic offline tests; no public API or real venue data."""
import sqlite3
import unittest
from menu_catalog_store import initialize, list_items, upsert_item

class MenuCatalogStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        self.item = dict(item_id='coffee', category='drink', name='Fictional Coffee', price_cents=350, available=True)

    def tearDown(self):
        self.db.close()

    def test_venue_isolation_with_same_item_id(self):
        upsert_item(self.db, venue_id='fictional-a', **self.item)
        upsert_item(self.db, venue_id='fictional-b', **{**self.item, 'price_cents': 450})
        self.assertEqual(list_items(self.db, venue_id='fictional-a')[0]['price_cents'], 350)
        self.assertEqual(list_items(self.db, venue_id='fictional-b')[0]['price_cents'], 450)
        self.assertEqual(list_items(self.db, venue_id='fictional-c'), [])

    def test_upsert_preserves_stable_id_and_availability(self):
        upsert_item(self.db, venue_id='fictional-a', **self.item)
        upsert_item(self.db, venue_id='fictional-a', **{**self.item, 'available': False})
        self.assertEqual(list_items(self.db, venue_id='fictional-a'), [dict(id='coffee', category='drink', name='Fictional Coffee', price_cents=350, available=False, currency='EUR')])

    def test_reject_invalid_prices_and_types(self):
        for price in (-1, True, 1.5, 100000001):
            with self.subTest(price=price), self.assertRaises(ValueError):
                upsert_item(self.db, venue_id='fictional-a', **{**self.item, 'price_cents': price})
        with self.assertRaises(ValueError):
            upsert_item(self.db, venue_id='fictional-a', **{**self.item, 'available': 1})

    def test_reject_missing_venue_and_bad_category(self):
        with self.assertRaises(ValueError):
            list_items(self.db, venue_id='')
        with self.assertRaises(ValueError):
            upsert_item(self.db, venue_id='fictional-a', **{**self.item, 'category': 'service'})

if __name__ == '__main__':
    unittest.main()
