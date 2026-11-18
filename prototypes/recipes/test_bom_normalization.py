import sqlite3, unittest
from fractions import Fraction
from recipe_bom import initialize, add_ingredient, add_component, recipe_summary

class NormalizationTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.execute('PRAGMA foreign_keys=ON')
        initialize(self.db)
        add_ingredient(self.db,venue='A',ingredient='flour',unit='mg',cost_cents_per_1000=2)
        add_ingredient(self.db,venue='B',ingredient='flour',unit='mg',cost_cents_per_1000=4)
    def tearDown(self):
        self.db.close()
    def test_grams_to_mg_and_cost(self):
        add_component(self.db,venue='A',recipe='bread',ingredient='flour',quantity=2,unit='g')
        s=recipe_summary(self.db,authorized_venue='A',recipe='bread')
        self.assertEqual(s['components'][0]['quantity'],2000)
        self.assertEqual(s['estimated_cost_cents'],4)
    def test_fractional_grams_exact(self):
        add_component(self.db,venue='A',recipe='bread',ingredient='flour',quantity=Fraction(1,2),unit='g')
        self.assertEqual(recipe_summary(self.db,authorized_venue='A',recipe='bread')['components'][0]['quantity'],500)
    def test_reject_fractional_base_unit_without_insert(self):
        with self.assertRaises(ValueError):
            add_component(self.db,venue='A',recipe='bread',ingredient='flour',quantity=Fraction(1,2000),unit='g')
        self.assertIsNone(recipe_summary(self.db,authorized_venue='A',recipe='bread'))
    def test_reject_dimension_mismatch(self):
        with self.assertRaises(ValueError):
            add_component(self.db,venue='A',recipe='bread',ingredient='flour',quantity=1,unit='ml')
    def test_reject_cross_venue_missing_ingredient(self):
        with self.assertRaises(ValueError):
            add_component(self.db,venue='C',recipe='bread',ingredient='flour',quantity=1,unit='g')
    def test_reject_boolean_quantity(self):
        with self.assertRaises(ValueError):
            add_component(self.db,venue='A',recipe='bread',ingredient='flour',quantity=True,unit='g')

if __name__=='__main__': unittest.main()
