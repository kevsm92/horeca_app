"""Offline, non-posting credit-request draft for short deliveries (synthetic only)."""
from dataclasses import dataclass

@dataclass(frozen=True)
class CreditDraft:
    venue_id: str
    purchase_order_id: str
    sku: str
    missing_units: int
    requested_cents: int
    status: str = "human_review_required"

def draft_short_delivery_credit(*, venue_id: str, purchase_order_id: str,
                                sku: str, ordered_units: int,
                                delivered_units: int, unit_price_cents: int) -> CreditDraft | None:
    if not all(isinstance(x, str) and x.strip() for x in (venue_id, purchase_order_id, sku)):
        raise ValueError("missing identity")
    if any(type(x) is not int or x < 0 for x in (ordered_units, delivered_units, unit_price_cents)):
        raise ValueError("invalid nonnegative integer")
    if ordered_units == 0 or unit_price_cents == 0:
        raise ValueError("purchase line must have positive quantity and price")
    if delivered_units >= ordered_units:
        return None
    missing = ordered_units - delivered_units
    return CreditDraft(venue_id, purchase_order_id, sku, missing, missing * unit_price_cents)

if __name__ == "__main__":
    import unittest
    class Tests(unittest.TestCase):
        def test_short(self):
            d = draft_short_delivery_credit(venue_id="synthetic-v", purchase_order_id="PO-1", sku="SYN-1", ordered_units=10, delivered_units=7, unit_price_cents=250)
            self.assertEqual((d.missing_units, d.requested_cents, d.status), (3, 750, "human_review_required"))
        def test_exact_or_excess_never_generates_credit(self):
            for qty in (10, 12):
                self.assertIsNone(draft_short_delivery_credit(venue_id="v", purchase_order_id="p", sku="s", ordered_units=10, delivered_units=qty, unit_price_cents=250))
        def test_invalid_and_bool_rejected(self):
            for qty in (-1, True):
                with self.assertRaises(ValueError):
                    draft_short_delivery_credit(venue_id="v", purchase_order_id="p", sku="s", ordered_units=10, delivered_units=qty, unit_price_cents=250)
        def test_missing_identity_rejected(self):
            with self.assertRaises(ValueError):
                draft_short_delivery_credit(venue_id="", purchase_order_id="p", sku="s", ordered_units=10, delivered_units=8, unit_price_cents=250)
    unittest.main(verbosity=2)
