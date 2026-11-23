import unittest
from three_way_hold import preview_match_hold


class MatchHoldTests(unittest.TestCase):
    def call(self, **changes):
        data = dict(venue_id="fictional-v", po_id="PO-1", sku="SYN-1",
                    ordered_units=10, delivered_units=10, quarantined_units=0,
                    rejected_units=0, invoiced_units=10,
                    agreed_unit_cents=250, invoiced_unit_cents=250)
        data.update(changes)
        return preview_match_hold(**data)

    def test_clean_still_requires_human_signoff(self):
        result = self.call()
        self.assertEqual(result.payable_ceiling_cents, 2500)
        self.assertEqual(result.reasons, ("manual_three_way_signoff_required",))
        self.assertFalse(result.posted)

    def test_quarantine_and_overinvoice_hold(self):
        result = self.call(quarantined_units=3, rejected_units=2)
        self.assertEqual(result.accepted_units, 5)
        self.assertEqual(result.payable_ceiling_cents, 1250)
        self.assertIn("invoice_quantity_differs_from_accepted", result.reasons)

    def test_overdelivery_and_price_difference(self):
        result = self.call(delivered_units=12, invoiced_units=12, invoiced_unit_cents=300)
        self.assertEqual(result.payable_ceiling_cents, 2500)
        self.assertIn("accepted_exceeds_ordered", result.reasons)
        self.assertIn("invoice_price_differs_from_po", result.reasons)

    def test_underinvoice_ceiling(self):
        self.assertEqual(self.call(invoiced_units=4, invoiced_unit_cents=200).payable_ceiling_cents, 800)

    def test_invalid_and_cross_venue_identity(self):
        for changes in ({"venue_id": " "}, {"ordered_units": True},
                        {"quarantined_units": 11}, {"rejected_units": -1},
                        {"agreed_unit_cents": 0}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.call(**changes)
        self.assertEqual(self.call(venue_id="fictional-v2").venue_id, "fictional-v2")


if __name__ == "__main__":
    unittest.main()
