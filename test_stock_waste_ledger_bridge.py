"""Synthetic tenant-isolated SQLite waste preview regression tests."""
import sqlite3
import unittest
from prototypes.inventory.inventory_ledger import initialize, add_ingredient, post_event, balance
from stock_waste_ledger_bridge import preview_waste_from_ledger


class WasteLedgerBridgeTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        initialize(self.db)
        add_ingredient(self.db, 'alpha', 'milk', 'Synthetic milk', 'ml')
        add_ingredient(self.db, 'beta', 'milk', 'Synthetic milk', 'g')
        post_event(self.db, 'alpha', 'milk', 'receipt1', 100, 'receipt')
        post_event(self.db, 'beta', 'milk', 'receipt1', 5, 'receipt')

    def tearDown(self):
        self.db.close()

    def test_trusted_unit_and_balance(self):
        result = preview_waste_from_ledger(self.db, venue_id='alpha',
            ingredient_id='milk', waste_units=20, reason='spoilage')
        self.assertEqual((result['unit'], result['projected_units']), ('ml', 80))
        self.assertFalse(result['posted'])
        self.assertTrue(result['requires_review'])

    def test_venue_isolation(self):
        with self.assertRaises(ValueError):
            preview_waste_from_ledger(self.db, venue_id='alpha', ingredient_id='missing',
                waste_units=1, reason='spoilage')
        result = preview_waste_from_ledger(self.db, venue_id='beta',
            ingredient_id='milk', waste_units=2, reason='damage')
        self.assertEqual((result['unit'], result['projected_units']), ('g', 3))

    def test_overdraw_and_invalid_values_do_not_post(self):
        before = self.db.execute('SELECT COUNT(*) FROM stock_events').fetchone()[0]
        for amount in (0, 101, True, 1.5, -1):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                preview_waste_from_ledger(self.db, venue_id='alpha',
                    ingredient_id='milk', waste_units=amount, reason='spoilage')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM stock_events').fetchone()[0], before)
        self.assertEqual(balance(self.db, 'alpha', 'milk'), 100)

    def test_other_reason_requires_note(self):
        with self.assertRaises(ValueError):
            preview_waste_from_ledger(self.db, venue_id='alpha', ingredient_id='milk',
                waste_units=1, reason='other')

    def test_invalid_identifier(self):
        with self.assertRaises(ValueError):
            preview_waste_from_ledger(self.db, venue_id="alpha' OR 1=1 --",
                ingredient_id='milk', waste_units=1, reason='spoilage')


if __name__ == '__main__':
    unittest.main()
