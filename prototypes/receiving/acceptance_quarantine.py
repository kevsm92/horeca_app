"""Offline fictional delivery acceptance preview; no stock posting or supplier contact."""
from dataclasses import dataclass
import unittest


@dataclass(frozen=True)
class AcceptancePreview:
    venue_id: str
    po_id: str
    sku: str
    delivered_units: int
    accepted_units: int
    quarantined_units: int
    rejected_units: int
    accepted_value_cents: int
    review_reasons: tuple[str, ...]
    status: str = "human_review_required"
    posted: bool = False


def preview_acceptance(*, venue_id: str, po_id: str, sku: str,
                       delivered_units: int, damaged_units: int,
                       temperature_uncertain_units: int, rejected_units: int,
                       unit_price_cents: int) -> AcceptancePreview:
    """Disjoint condition counts; uncertainty is quarantined, never auto-accepted."""
    if any(type(x) is not str or not x.strip() for x in (venue_id, po_id, sku)):
        raise ValueError("missing receiving identity")
    numbers = (delivered_units, damaged_units, temperature_uncertain_units,
               rejected_units, unit_price_cents)
    if any(type(x) is not int or x < 0 for x in numbers):
        raise ValueError("quantities and cents must be nonnegative integers")
    if unit_price_cents == 0:
        raise ValueError("unit price must be positive")
    quarantined = damaged_units + temperature_uncertain_units
    if quarantined + rejected_units > delivered_units:
        raise ValueError("condition counts exceed delivered units")
    accepted = delivered_units - quarantined - rejected_units
    reasons = []
    if damaged_units:
        reasons.append("damaged_units_quarantined")
    if temperature_uncertain_units:
        reasons.append("temperature_uncertain_units_quarantined")
    if rejected_units:
        reasons.append("rejected_units")
    return AcceptancePreview(venue_id, po_id, sku, delivered_units, accepted,
                             quarantined, rejected_units, accepted * unit_price_cents,
                             tuple(reasons))


class AcceptanceTests(unittest.TestCase):
    def test_partition_and_nonposting(self):
        p = preview_acceptance(venue_id="fictional-v", po_id="PO-1", sku="FOOD-1",
                               delivered_units=12, damaged_units=2,
                               temperature_uncertain_units=3, rejected_units=1,
                               unit_price_cents=250)
        self.assertEqual((p.accepted_units, p.quarantined_units,
                          p.rejected_units, p.accepted_value_cents), (6, 5, 1, 1500))
        self.assertFalse(p.posted)
        self.assertEqual(len(p.review_reasons), 3)

    def test_clean_delivery_still_requires_review(self):
        p = preview_acceptance(venue_id="v", po_id="p", sku="s", delivered_units=2,
                               damaged_units=0, temperature_uncertain_units=0,
                               rejected_units=0, unit_price_cents=100)
        self.assertEqual((p.accepted_units, p.status, p.posted),
                         (2, "human_review_required", False))

    def test_invalid_partition_and_types(self):
        base = dict(venue_id="v", po_id="p", sku="s", delivered_units=2,
                    damaged_units=0, temperature_uncertain_units=0,
                    rejected_units=0, unit_price_cents=100)
        for key, value in (("damaged_units", 3), ("delivered_units", True),
                           ("rejected_units", -1), ("unit_price_cents", 0),
                           ("venue_id", "")):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                preview_acceptance(**(base | {key: value}))

    def test_all_quarantined(self):
        p = preview_acceptance(venue_id="v", po_id="p", sku="s", delivered_units=2,
                               damaged_units=0, temperature_uncertain_units=2,
                               rejected_units=0, unit_price_cents=100)
        self.assertEqual((p.accepted_units, p.accepted_value_cents), (0, 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
