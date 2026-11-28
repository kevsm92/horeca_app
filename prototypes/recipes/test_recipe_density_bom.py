import sqlite3
import unittest
from recipe_bom import initialize, add_ingredient, recipe_summary
from recipe_density_store import initialize_density_store, append_density_revision
from recipe_density_bom import add_approved_density_component


class DensityBOMTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        initialize_density_store(self.db)
        add_ingredient(self.db, venue='fictional-a', ingredient='oil', unit='mg',
                       cost_cents_per_1000=100)
        add_ingredient(self.db, venue='fictional-b', ingredient='oil', unit='mg',
                       cost_cents_per_1000=100)

    def tearDown(self):
        self.db.close()

    def approve(self, status='approved', revision=1):
        append_density_revision(self.db, authorized_venue='fictional-a', ingredient_id='oil',
                                revision=revision, status=status,
                                mg_per_ml_numerator=900, mg_per_ml_denominator=1)

    def add(self, venue='fictional-a', quantity=2, unit='ml', recipe='sauce'):
        add_approved_density_component(self.db, authorized_venue=venue, recipe=recipe,
                                       ingredient='oil', quantity=quantity, unit=unit)

    def test_approved_conversion_and_cost(self):
        self.approve()
        self.add()
        summary = recipe_summary(self.db, authorized_venue='fictional-a', recipe='sauce')
        self.assertEqual(summary['components'][0]['quantity'], 1800)
        self.assertEqual(summary['estimated_cost_cents'], 180)

    def test_missing_and_cross_venue_density_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'approved'):
            self.add()
        self.approve()
        with self.assertRaisesRegex(ValueError, 'approved'):
            self.add(venue='fictional-b')

    def test_revoked_density_fails_closed(self):
        self.approve()
        self.approve(status='revoked', revision=2)
        with self.assertRaisesRegex(ValueError, 'approved'):
            self.add()

    def test_non_integral_conversion_rejected_without_component(self):
        self.approve()
        add_ingredient(self.db, venue='fictional-a', ingredient='oil-volume', unit='ml',
                       cost_cents_per_1000=100)
        append_density_revision(self.db, authorized_venue='fictional-a',
                                ingredient_id='oil-volume', revision=1, status='approved',
                                mg_per_ml_numerator=900, mg_per_ml_denominator=1)
        with self.assertRaisesRegex(ValueError, 'fractional'):
            add_approved_density_component(self.db, authorized_venue='fictional-a',
                recipe='sauce', ingredient='oil-volume', quantity=1, unit='mg')
        self.assertIsNone(recipe_summary(self.db, authorized_venue='fictional-a', recipe='sauce'))

    def test_same_dimension_does_not_require_density(self):
        self.add(quantity=2, unit='g')
        self.assertEqual(recipe_summary(self.db, authorized_venue='fictional-a', recipe='sauce')
                         ['components'][0]['quantity'], 2000)

    def test_unknown_ingredient_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unknown'):
            add_approved_density_component(self.db, authorized_venue='fictional-a',
                recipe='sauce', ingredient='not-present', quantity=1, unit='ml')


if __name__ == '__main__':
    unittest.main()
