import unittest
from recipe_approved_conversion import convert_with_approved_density


class ApprovedDensityTests(unittest.TestCase):
    def setUp(self):
        self.approval = dict(venue_id='fictional-a', ingredient_id='fictional-oil',
                             status='approved', revision=1,
                             mg_per_ml_numerator=900, mg_per_ml_denominator=1)

    def convert(self, quantity, source, target, **kwargs):
        return convert_with_approved_density(
            quantity, source, target,
            authorized_venue=kwargs.get('venue', 'fictional-a'),
            ingredient_id=kwargs.get('ingredient', 'fictional-oil'),
            approval=kwargs.get('approval', self.approval))

    def test_volume_to_mass_exact(self):
        self.assertEqual(self.convert(2, 'l', 'g'), 1800)

    def test_mass_to_volume_exact(self):
        self.assertEqual(self.convert(900, 'g', 'ml'), 1000)

    def test_tenant_and_ingredient_isolation(self):
        for kwargs in ({'venue': 'fictional-b'}, {'ingredient': 'fictional-milk'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.convert(1, 'ml', 'mg', **kwargs)

    def test_revoked_and_unversioned(self):
        for patch in ({'status': 'revoked'}, {'revision': 0}, {'revision': True}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.convert(1, 'ml', 'mg', approval={**self.approval, **patch})

    def test_invalid_ratio(self):
        for bad in (0, -1, True, 1.2):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.convert(1, 'ml', 'mg',
                             approval={**self.approval, 'mg_per_ml_numerator': bad})

    def test_no_implicit_conversion(self):
        for units in (('g', 'kg'), ('piece', 'ml'), ('oz', 'g')):
            with self.subTest(units=units), self.assertRaises(ValueError):
                self.convert(1, *units)

    def test_no_rounding(self):
        with self.assertRaises(ValueError):
            self.convert(1, 'mg', 'ml')

    def test_positive_quantity_only(self):
        for bad in (0, -1, True, 1.1):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.convert(bad, 'ml', 'mg')


if __name__ == '__main__':
    unittest.main()
