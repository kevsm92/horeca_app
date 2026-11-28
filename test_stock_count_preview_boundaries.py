"""Synthetic stock-count preview boundary regressions; no stock mutations.

Run: python -m unittest -v test_stock_count_preview_boundaries
"""
import unittest

from stock_count_preview import MAX_UNITS, preview_count


class StockCountPreviewBoundaries(unittest.TestCase):
    def test_equal_count_is_review_free_and_unposted(self):
        result = preview_count(ledger_units=12, counted_units=12, unit='each')
        self.assertEqual(result['variance_units'], 0)
        self.assertFalse(result['requires_review'])
        self.assertIs(result['posted'], False)

    def test_shortage_is_negative_and_reviewable(self):
        result = preview_count(ledger_units=50, counted_units=8, unit='g')
        self.assertEqual(result['variance_units'], -42)
        self.assertTrue(result['requires_review'])
        self.assertFalse(result['posted'])

    def test_surplus_is_positive_and_reviewable(self):
        result = preview_count(ledger_units=3, counted_units=11, unit='ml')
        self.assertEqual(result['variance_units'], 8)
        self.assertTrue(result['requires_review'])
        self.assertFalse(result['posted'])

    def test_maximum_bounded_variance(self):
        result = preview_count(ledger_units=MAX_UNITS, counted_units=0, unit='each')
        self.assertEqual(result['variance_units'], -MAX_UNITS)
        self.assertTrue(result['requires_review'])

    def test_invalid_counts_rejected_without_coercion(self):
        for value in (-1, MAX_UNITS + 1, True, False, 2.0, '2', None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    preview_count(ledger_units=value, counted_units=0, unit='each')
                with self.assertRaises(ValueError):
                    preview_count(ledger_units=0, counted_units=value, unit='each')

    def test_unknown_or_non_string_unit_rejected(self):
        for unit in ('kg', 'G', '', None, 1, ['g']):
            with self.subTest(unit=unit):
                with self.assertRaises(ValueError):
                    preview_count(ledger_units=1, counted_units=1, unit=unit)


if __name__ == '__main__':
    unittest.main()
