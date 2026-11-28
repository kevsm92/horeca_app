import unittest
from fractions import Fraction
from recipe_unit_conversion import normalize_quantity, convert_quantity

class ConversionTests(unittest.TestCase):
    def test_mass_exact(self):
        self.assertEqual(normalize_quantity('0.125', 'kg'), (Fraction(125000), 'mg'))
        self.assertEqual(convert_quantity('125', 'g', 'kg'), Fraction(1, 8))
    def test_volume_exact(self):
        self.assertEqual(convert_quantity('0.25', 'l', 'ml'), Fraction(250))
    def test_discrete_count(self):
        self.assertEqual(normalize_quantity(3, 'each'), (Fraction(3), 'each'))
        with self.assertRaises(ValueError): normalize_quantity('0.5', 'each')
    def test_no_density_guess(self):
        with self.assertRaisesRegex(ValueError, 'incompatible'): convert_quantity(1, 'l', 'kg')
    def test_reject_invalid(self):
        for quantity in (0, -1, True, 0.5, 'nan', 'inf', 'bad'):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError): normalize_quantity(quantity, 'g')
    def test_reject_unknown_units(self):
        for unit in ('cup', 'oz', '', None):
            with self.subTest(unit=unit), self.assertRaises(ValueError): normalize_quantity(1, unit)
    def test_no_float_rounding(self):
        self.assertEqual(convert_quantity('0.001', 'g', 'mg'), Fraction(1))

if __name__ == '__main__': unittest.main()
