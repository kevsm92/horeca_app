import unittest
from receiving_shortage import preview_shortage


class ShortageTests(unittest.TestCase):
    def setUp(self):
        self.base = dict(venue_id="fictional-v", po_id="PO-12", sku="MILK-1",
                         ordered_units=12, previously_accepted_units=4,
                         delivered_units=6, quarantined_units=1,
                         rejected_units=2, agreed_unit_cents=250)

    def test_partial_receipt_and_nonposting(self):
        p = preview_shortage(**self.base)
        self.assertEqual((p.newly_accepted_units, p.outstanding_units,
                          p.outstanding_value_cents), (3, 5, 1250))
        self.assertEqual(len(p.reasons), 3)
        self.assertFalse(p.posted)
        self.assertEqual(p.status, "human_review_required")

    def test_fully_fulfilled_still_needs_signoff(self):
        p = preview_shortage(**(self.base | dict(previously_accepted_units=9,
                            quarantined_units=0, rejected_units=0,
                            delivered_units=3)))
        self.assertEqual((p.outstanding_units, p.reasons),
                         (0, ("manual_receipt_signoff_required",)))

    def test_invalid_and_overdelivery_fail_closed(self):
        for change in (dict(venue_id=""), dict(ordered_units=True),
                       dict(rejected_units=7), dict(previously_accepted_units=10),
                       dict(agreed_unit_cents=0), dict(delivered_units=-1)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                preview_shortage(**(self.base | change))

    def test_venue_identity_preserved(self):
        p = preview_shortage(**(self.base | dict(venue_id="fictional-other")))
        self.assertEqual(p.venue_id, "fictional-other")
        self.assertNotEqual(p.venue_id, self.base["venue_id"])


if __name__ == "__main__":
    unittest.main()
