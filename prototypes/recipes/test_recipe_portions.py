import unittest
from recipe_portions import portion_costs


class PortionCostsTests(unittest.TestCase):
    def test_exact_allocation(self):
        self.assertEqual(portion_costs(600, 3), [200, 200, 200])

    def test_remainder_conserved(self):
        result = portion_costs(101, 4)
        self.assertEqual(result, [26, 25, 25, 25])
        self.assertEqual(sum(result), 101)

    def test_zero_cost_and_more_portions_than_cents(self):
        self.assertEqual(portion_costs(0, 2), [0, 0])
        self.assertEqual(portion_costs(2, 4), [1, 1, 0, 0])

    def test_rejects_invalid_inputs(self):
        for value in (-1, 1.5, True, '12', None):
            with self.subTest(cost=value), self.assertRaises(ValueError):
                portion_costs(value, 2)
        for value in (0, -1, True, 1.5, '3', None):
            with self.subTest(yield_count=value), self.assertRaises(ValueError):
                portion_costs(100, value)


if __name__ == '__main__':
    unittest.main()
