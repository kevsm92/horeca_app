import unittest
from fractions import Fraction
from recipe_units import normalize_quantity

class RecipeUnitTests(unittest.TestCase):
    def test_mass(self):
        self.assertEqual(normalize_quantity(2, 'kg', 'mg'), 2000000)
        self.assertEqual(normalize_quantity(Fraction(3, 2), 'g', 'mg'), 1500)

    def test_volume(self):
        self.assertEqual(normalize_quantity(Fraction(1, 4), 'l', 'ml'), 250)

    def test_count(self):
        self.assertEqual(normalize_quantity(3, 'piece', 'piece'), 3)

    def test_fractional_target_rejected(self):
        with self.assertRaises(ValueError):
            normalize_quantity(1, 'mg', 'g')

    def test_cross_dimension_rejected(self):
        for source, target in [('ml', 'mg'), ('piece', 'ml'), ('kg', 'piece')]:
            with self.subTest(source=source, target=target), self.assertRaises(ValueError):
                normalize_quantity(1, source, target)

    def test_invalid_input(self):
        for quantity in [0, -1, True, 1.2, '1']:
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                normalize_quantity(quantity, 'g', 'mg')
        with self.assertRaises(ValueError):
            normalize_quantity(1, 'oz', 'mg')

if __name__ == '__main__':
    unittest.main()
