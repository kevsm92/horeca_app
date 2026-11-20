import unittest
from inventory_par_replenishment import suggest_replenishment


class ParSuggestionTests(unittest.TestCase):
    def calculate(self, **overrides):
        params = dict(venue_id='synthetic-A', sku_venue_id='synthetic-A',
                      on_hand=12, reserved=2, par_level=10,
                      target_level=20, pack_size=6)
        params.update(overrides)
        return suggest_replenishment(**params)

    def test_exact_par_no_reorder(self):
        self.assertEqual(self.calculate()['suggested_units'], 0)

    def test_below_par_rounds_to_pack(self):
        r = self.calculate(on_hand=11)
        self.assertEqual((r['suggested_units'], r['suggested_packs']), (12, 2))
        self.assertFalse(r['purchase_order_created'])

    def test_reservations_reduce_available(self):
        self.assertEqual(self.calculate(on_hand=15, reserved=9)['available_units'], 6)

    def test_negative_available_not_clipped(self):
        r = self.calculate(on_hand=1, reserved=5)
        self.assertEqual((r['available_units'], r['suggested_units']), (-4, 24))

    def test_other_venue_denied(self):
        with self.assertRaises(PermissionError):
            self.calculate(sku_venue_id='synthetic-B')

    def test_no_venue_denied(self):
        with self.assertRaises(ValueError):
            self.calculate(venue_id='')

    def test_invalid_quantities_rejected(self):
        for field, value in [('on_hand', -1), ('reserved', 1.5),
                             ('par_level', True), ('pack_size', 0)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.calculate(**{field: value})

    def test_target_below_par_rejected(self):
        with self.assertRaises(ValueError):
            self.calculate(target_level=9)

    def test_no_supplier_or_order_side_effect(self):
        self.assertEqual(self.calculate(on_hand=0)['status'], 'review_suggestion')


if __name__ == '__main__':
    unittest.main()
