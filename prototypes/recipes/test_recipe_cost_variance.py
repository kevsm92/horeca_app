"""Synthetic-only cost variance regression checks."""
import unittest
from recipe_cost_variance import compare_recipe_cost_quotes


def quote(cost, portions=3, recipe='fictional-soup'):
    base, rem = divmod(cost, portions)
    return {'recipe_id': recipe, 'approved_yield': portions,
            'estimated_batch_cost_cents': cost,
            'estimated_portion_costs_cents': [base + (i < rem) for i in range(portions)]}


class CostVarianceTests(unittest.TestCase):
    def test_increase_preserves_integer_cents(self):
        result = compare_recipe_cost_quotes(quote(100), quote(101))
        self.assertEqual(result['batch_cost_delta_cents'], 1)
        self.assertEqual(result['comparison_status'], 'estimate_only_not_menu_price')

    def test_decrease_and_zero(self):
        self.assertEqual(compare_recipe_cost_quotes(quote(5), quote(0))['batch_cost_delta_cents'], -5)

    def test_rejects_changed_recipe_or_yield(self):
        for changed in (quote(100, recipe='other'), quote(100, portions=2)):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                compare_recipe_cost_quotes(quote(100), changed)

    def test_rejects_invalid_or_nonconserving_snapshots(self):
        for invalid in (None, {}, {**quote(3), 'estimated_batch_cost_cents': True},
                        {**quote(3), 'estimated_portion_costs_cents': [1, 1, 0]},
                        {**quote(3), 'estimated_portion_costs_cents': [1, -1, 3]},
                        {**quote(3), 'approved_yield': 0}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                compare_recipe_cost_quotes(quote(3), invalid)

    def test_input_unchanged(self):
        old, new = quote(10), quote(11)
        before = (old.copy(), new.copy())
        compare_recipe_cost_quotes(old, new)
        self.assertEqual((old, new), before)


if __name__ == '__main__':
    unittest.main()
