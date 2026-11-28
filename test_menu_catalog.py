import sqlite3
import unittest
from menu_catalog import initialize, add_item, list_items, seed_fictional


class MenuCatalogTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)

    def tearDown(self):
        self.db.close()

    def test_venue_isolation_and_fictional_seed_idempotency(self):
        seed_fictional(self.db, 'venue-a')
        seed_fictional(self.db, 'venue-a')
        self.assertEqual(len(list_items(self.db, 'venue-a')), 2)
        self.assertEqual(list_items(self.db, 'venue-b'), [])
        self.assertEqual({x['category'] for x in list_items(self.db, 'venue-a')}, {'food','drink'})
        self.assertEqual(list_items(self.db, 'venue-a')[0]['currency'], 'EUR')

    def test_integer_cents_and_availability(self):
        for invalid in [True, 3.5, '200', -1]:
            with self.assertRaises((ValueError, sqlite3.IntegrityError)):
                add_item(self.db, 'a', 'id', 'food', 'Dish', invalid)
        add_item(self.db, 'a', 'id', 'food', 'Dish', 0, False)
        self.assertEqual(list_items(self.db, 'a')[0]['available'], False)
        self.assertEqual(list_items(self.db, 'a')[0]['price_cents'], 0)

    def test_sql_constraints_and_scope(self):
        with self.assertRaises(ValueError):
            list_items(self.db, '')
        with self.assertRaises(sqlite3.IntegrityError):
            add_item(self.db, 'a', 'x', 'service', 'Dish', 200)
        with self.assertRaises(sqlite3.IntegrityError):
            add_item(self.db, 'a', 'x', 'food', '', 200)
        add_item(self.db, 'a', 'x', 'food', 'Dish', 200)
        with self.assertRaises(sqlite3.IntegrityError):
            add_item(self.db, 'a', 'x', 'food', 'Duplicate', 200)
        add_item(self.db, 'b', 'x', 'drink', 'Drink', 300)
        self.assertEqual(list_items(self.db, 'b')[0]['name'], 'Drink')


if __name__ == '__main__':
    unittest.main()
