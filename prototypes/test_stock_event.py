import unittest
from stock_event import Deduction, plan_deductions


class DeductionTests(unittest.TestCase):
    def setUp(self):
        self.recipes = {'coffee': (Deduction('beans', 18000), Deduction('milk', 100000)), 'latte': (Deduction('beans', 18000), Deduction('milk', 200000))}

    def test_aggregate_deterministic(self):
        key, entries = plan_deductions('synthetic-42', (('latte', 2), ('coffee', 1)), self.recipes)
        self.assertEqual(key, 'order:synthetic-42:stock-deduct:v1')
        self.assertEqual(entries, (Deduction('beans', 54000), Deduction('milk', 500000)))

    def test_replay_same_plan(self):
        args = ('synthetic-42', (('coffee', 1),), self.recipes)
        self.assertEqual(plan_deductions(*args), plan_deductions(*args))

    def test_invalid_inputs(self):
        for lines in ((), (('coffee', 0),), (('coffee', True),), (('unknown', 1),)):
            with self.subTest(lines=lines), self.assertRaises(ValueError):
                plan_deductions('synthetic-42', lines, self.recipes)
        with self.assertRaises(ValueError):
            plan_deductions('', (('coffee', 1),), self.recipes)
        with self.assertRaises(ValueError):
            plan_deductions('x', (('coffee', 1),), {'coffee': (Deduction('beans', -1),)})


if __name__ == '__main__':
    unittest.main()
