import sqlite3
import unittest
from recipe_bom import initialize,add_ingredient,add_component,recipe_summary
class RecipeTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(':memory:');self.db.execute('PRAGMA foreign_keys=ON');initialize(self.db)
  add_ingredient(self.db,venue='A',ingredient='milk',unit='ml',cost_cents_per_1000=200,allergens=['milk'])
  add_ingredient(self.db,venue='B',ingredient='milk',unit='ml',cost_cents_per_1000=900)
 def tearDown(self):self.db.close()
 def test_cost_and_allergens(self):
  add_component(self.db,venue='A',recipe='latte',ingredient='milk',quantity=125,unit='ml')
  self.assertEqual(recipe_summary(self.db,authorized_venue='A',recipe='latte')['estimated_cost_cents'],25)
  self.assertEqual(recipe_summary(self.db,authorized_venue='A',recipe='latte')['allergens'],['milk'])
 def test_tenant_isolation(self):
  add_component(self.db,venue='A',recipe='latte',ingredient='milk',quantity=125,unit='ml')
  self.assertIsNone(recipe_summary(self.db,authorized_venue='B',recipe='latte'))
 def test_unit_mismatch(self):
  with self.assertRaises(ValueError):add_component(self.db,venue='A',recipe='latte',ingredient='milk',quantity=1,unit='mg')
 def test_missing_ingredient(self):
  with self.assertRaises(ValueError):add_component(self.db,venue='A',recipe='latte',ingredient='missing',quantity=1,unit='ml')
 def test_invalid_quantities_and_costs(self):
  for n in (0,-1,True,1.5):
   with self.assertRaises(ValueError):add_component(self.db,venue='A',recipe='latte',ingredient='milk',quantity=n,unit='ml')
  with self.assertRaises(ValueError):add_ingredient(self.db,venue='A',ingredient='bad',unit='ml',cost_cents_per_1000=-1)
 def test_rounding_up(self):
  add_component(self.db,venue='A',recipe='sip',ingredient='milk',quantity=1,unit='ml')
  self.assertEqual(recipe_summary(self.db,authorized_venue='A',recipe='sip')['estimated_cost_cents'],1)
if __name__=='__main__':unittest.main()
