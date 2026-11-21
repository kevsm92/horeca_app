import unittest
from stock_waste_preview import preview_waste


BASE = dict(venue_id='synthetic-venue-a', sku_venue_id='synthetic-venue-a',
            ledger_units=100, waste_units=25, unit='g', reason='spoilage')


class WastePreviewTests(unittest.TestCase):
    def preview(self, **changes):
        return preview_waste(**(BASE | changes))

    def test_preview_does_not_post(self):
        self.assertEqual(self.preview()['projected_units'], 75)
        self.assertFalse(self.preview()['posted'])
        self.assertTrue(self.preview()['requires_review'])

    def test_full_stock_waste_is_allowed_for_review(self):
        self.assertEqual(self.preview(waste_units=100)['projected_units'], 0)

    def test_cross_venue_rejected(self):
        with self.assertRaises(PermissionError):
            self.preview(sku_venue_id='synthetic-venue-b')

    def test_zero_and_overdraw_rejected(self):
        for value in (0, 101, -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.preview(waste_units=value)

    def test_boolean_and_float_quantities_rejected(self):
        for value in (True, 1.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.preview(waste_units=value)

    def test_unapproved_reason_rejected(self):
        with self.assertRaises(ValueError):
            self.preview(reason='unexplained')

    def test_other_requires_explanation(self):
        with self.assertRaises(ValueError):
            self.preview(reason='other')
        self.assertEqual(self.preview(reason='other', note='Synthetic breakage')['reason'], 'other')

    def test_invalid_units_rejected(self):
        with self.assertRaises(ValueError):
            self.preview(unit='kg')

    def test_note_limit(self):
        with self.assertRaises(ValueError):
            self.preview(note='x' * 501)

    def test_empty_venue_rejected(self):
        with self.assertRaises(ValueError):
            self.preview(venue_id=' ')


if __name__ == '__main__':
    unittest.main()
