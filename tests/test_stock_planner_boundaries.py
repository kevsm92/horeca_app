"""Synthetic planner boundary tests; no real inventory is changed."""
import unittest
from prototypes.stock_event import Deduction, plan_deductions

class PlannerBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.recipes = {'latte': (Deduction('milk', 200), Deduction('beans', 18)),
                        'flat-white': (Deduction('milk', 150), Deduction('beans', 18))}

    def test_aggregates_shared_ingredients_in_stable_order(self):
        key, items = plan_deductions('order-7', (('latte', 2), ('flat-white', 1)), self.recipes)
        self.assertEqual(key, 'order:order-7:stock-deduct:v1')
        self.assertEqual(items, (Deduction('beans', 54), Deduction('milk', 550)))

    def test_repeated_planning_is_deterministic(self):
        first = plan_deductions('order-7', (('latte', 1),), self.recipes)
        self.assertEqual(first, plan_deductions('order-7', (('latte', 1),), self.recipes))

    def test_rejects_boolean_and_nonpositive_order_quantities(self):
        for amount in (True, False, 0, -1, 1.5, '2', None):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                plan_deductions('order-7', (('latte', amount),), self.recipes)

    def test_rejects_invalid_recipe_quantities(self):
        for amount in (True, 0, -1, 1.5, None):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                plan_deductions('order-7', (('latte', 1),), {'latte': (Deduction('milk', amount),)})

    def test_rejects_unknown_or_empty_recipe(self):
        for recipes in ({}, {'latte': ()}):
            with self.subTest(recipes=recipes), self.assertRaises(ValueError):
                plan_deductions('order-7', (('latte', 1),), recipes)

    def test_rejects_empty_order_and_identifier(self):
        for order_id, lines in (('', (('latte', 1),)), ('order-7', ())):
            with self.subTest(order_id=order_id), self.assertRaises(ValueError):
                plan_deductions(order_id, lines, self.recipes)

if __name__ == '__main__':
    unittest.main()
