"""Synthetic, offline regression tests for ledger-backed count preview."""
import sqlite3
import unittest
from prototypes.inventory.inventory_ledger import (
    add_ingredient, balance, initialize, post_event,
)
from stock_count_ledger_bridge import preview_count_from_ledger


class CountLedgerBridgeTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        initialize(self.db)
        add_ingredient(self.db, 'venue_a', 'milk', 'Synthetic milk', 'ml')
        add_ingredient(self.db, 'venue_b', 'milk', 'Synthetic milk', 'ml')
        post_event(self.db, 'venue_a', 'milk', 'receipt_a', 200, 'receipt')
        post_event(self.db, 'venue_b', 'milk', 'receipt_b', 90, 'receipt')

    def tearDown(self):
        self.db.close()

    def test_signed_variance_and_trusted_unit(self):
        result = preview_count_from_ledger(
            self.db, venue_id='venue_a', ingredient_id='milk', counted_units=180)
        self.assertEqual((result['unit'], result['ledger_units'],
                          result['variance_units']), ('ml', 200, -20))
        self.assertTrue(result['requires_review'])
        self.assertFalse(result['posted'])

    def test_exact_match_does_not_require_review(self):
        result = preview_count_from_ledger(
            self.db, venue_id='venue_a', ingredient_id='milk', counted_units=200)
        self.assertFalse(result['requires_review'])

    def test_cross_venue_isolation(self):
        result = preview_count_from_ledger(
            self.db, venue_id='venue_b', ingredient_id='milk', counted_units=90)
        self.assertEqual(result['ledger_units'], 90)
        with self.assertRaises(ValueError):
            preview_count_from_ledger(self.db, venue_id='venue_b',
                                      ingredient_id='missing', counted_units=1)

    def test_invalid_count_rejected(self):
        for count in (-1, True, 1.5, 1_000_000_001):
            with self.subTest(count=count), self.assertRaises(ValueError):
                preview_count_from_ledger(self.db, venue_id='venue_a',
                                          ingredient_id='milk', counted_units=count)

    def test_read_only_even_when_invalid(self):
        before = self.db.execute('SELECT COUNT(*) FROM stock_events').fetchone()[0]
        preview_count_from_ledger(self.db, venue_id='venue_a',
                                  ingredient_id='milk', counted_units=190)
        with self.assertRaises(ValueError):
            preview_count_from_ledger(self.db, venue_id='venue_a',
                                      ingredient_id='milk', counted_units=-1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM stock_events').fetchone()[0], before)
        self.assertEqual(balance(self.db, 'venue_a', 'milk'), 200)


if __name__ == '__main__':
    unittest.main()
