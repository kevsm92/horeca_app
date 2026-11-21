"""Synthetic regression tests for read-only inventory count variance."""
import unittest
from stock_count_preview import MAX_UNITS, preview_count


class CountPreviewTests(unittest.TestCase):
    def test_match(self):
        result = preview_count(ledger_units=15, counted_units=15, unit='each')
        self.assertEqual(result['variance_units'], 0)
        self.assertFalse(result['requires_review'])
        self.assertFalse(result['posted'])

    def test_shortage_and_surplus(self):
        for actual, expected in ((7, -3), (12, 2)):
            with self.subTest(actual=actual):
                result = preview_count(ledger_units=10, counted_units=actual, unit='g')
                self.assertEqual(result['variance_units'], expected)
                self.assertTrue(result['requires_review'])
                self.assertFalse(result['posted'])

    def test_invalid_quantities(self):
        for bad in (-1, True, 1.2, None, MAX_UNITS + 1):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    preview_count(ledger_units=bad, counted_units=0, unit='ml')
                with self.assertRaises(ValueError):
                    preview_count(ledger_units=0, counted_units=bad, unit='ml')

    def test_invalid_unit(self):
        for bad in ('kg', '', None, True, 1):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    preview_count(ledger_units=0, counted_units=0, unit=bad)

    def test_upper_bound(self):
        self.assertEqual(preview_count(ledger_units=MAX_UNITS,
                         counted_units=0, unit='each')['variance_units'], -MAX_UNITS)


if __name__ == '__main__':
    unittest.main()
