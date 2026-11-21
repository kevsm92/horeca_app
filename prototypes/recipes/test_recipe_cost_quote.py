"""Synthetic-only tests for venue-scoped recipe cost quoting."""
import sqlite3
import unittest
from recipe_bom import initialize, add_ingredient, add_component
from recipe_cost_quote import quote_recipe_portions


class RecipeCostQuoteTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('PRAGMA foreign_keys=ON')
        initialize(self.db)
        for venue, cost in [('venue-a', 1001), ('venue-b', 2000)]:
            add_ingredient(self.db, venue=venue, ingredient='fictional-flour',
                           unit='mg', cost_cents_per_1000=cost, allergens=('gluten',))
            add_component(self.db, venue=venue, recipe='fictional-bread',
                          ingredient='fictional-flour', quantity=1000, unit='mg')

    def tearDown(self):
        self.db.close()

    def test_cost_conservation_and_remainder(self):
        result = quote_recipe_portions(self.db, authorized_venue='venue-a',
                                       recipe='fictional-bread', approved_yield=3)
        self.assertEqual(result['estimated_portion_costs_cents'], [334, 334, 333])
        self.assertEqual(sum(result['estimated_portion_costs_cents']), 1001)
        self.assertEqual(result['pricing_status'], 'estimate_not_menu_price')
        self.assertEqual(result['allergen_status'], 'incomplete_supplier_verification')

    def test_venue_isolation(self):
        result = quote_recipe_portions(self.db, authorized_venue='venue-b',
                                       recipe='fictional-bread', approved_yield=2)
        self.assertEqual(result['estimated_portion_costs_cents'], [1000, 1000])
        self.assertIsNone(quote_recipe_portions(self.db, authorized_venue='venue-c',
                                                recipe='fictional-bread', approved_yield=2))

    def test_unknown_recipe(self):
        self.assertIsNone(quote_recipe_portions(self.db, authorized_venue='venue-a',
                                                recipe='missing', approved_yield=2))

    def test_rejects_invalid_yield(self):
        for value in (0, -1, True, 1.5, '2'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                quote_recipe_portions(self.db, authorized_venue='venue-a',
                                      recipe='fictional-bread', approved_yield=value)


if __name__ == '__main__':
    unittest.main()
