import unittest
from stock_par_eligible_preview import preview_par_gap


def stock(**overrides):
    data = dict(venue_id='v1', item_id='milk', eligible_units=4,
                withheld_units=3, ledger_modified=False, purchase_order_created=False)
    data.update(overrides)
    return data


class ParGapTests(unittest.TestCase):
    def calculate(self, **overrides):
        return preview_par_gap(venue_id='v1', item_id='milk', par_units=10,
                               eligible_stock=stock(**overrides))

    def test_withheld_does_not_count_toward_par(self):
        result = self.calculate()
        self.assertEqual(result['suggested_replenishment_units'], 6)
        self.assertTrue(result['requires_human_review'])
        self.assertFalse(result['purchase_order_created'])
        self.assertFalse(result['ledger_modified'])

    def test_above_par_has_zero_gap(self):
        self.assertEqual(self.calculate(eligible_units=12)['suggested_replenishment_units'], 0)

    def test_no_withheld_requires_no_review(self):
        self.assertFalse(self.calculate(withheld_units=0)['requires_human_review'])

    def test_reject_cross_venue(self):
        with self.assertRaises(PermissionError):
            self.calculate(venue_id='v2')

    def test_reject_other_ingredient(self):
        with self.assertRaises(ValueError):
            self.calculate(item_id='eggs')

    def test_reject_invalid_quantities(self):
        for value in (True, -1, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.calculate(eligible_units=value)

    def test_reject_mutated_preview(self):
        with self.assertRaises(ValueError):
            self.calculate(ledger_modified=True)

    def test_reject_invalid_par(self):
        for value in (-1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                preview_par_gap(venue_id='v1', item_id='milk', par_units=value,
                                eligible_stock=stock())


if __name__ == '__main__':
    unittest.main()
