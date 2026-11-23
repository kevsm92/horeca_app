"""Offline, synthetic-only shortage credit request draft; never posts or transmits."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CreditDraft:
    venue_id: str
    po_id: str
    sku: str
    missing_units: int
    requested_cents: int
    status: str = "human_review_required"


def draft_credit(venue_id, po_venue_id, receipt_venue_id, po_id, sku,
                 ordered_units, received_units, unit_price_cents):
    if not all(isinstance(s, str) and s.strip() for s in
               (venue_id, po_venue_id, receipt_venue_id, po_id, sku)):
        raise ValueError("missing identity")
    if venue_id != po_venue_id or venue_id != receipt_venue_id:
        raise ValueError("cross-venue reference")
    if any(type(n) is not int for n in (ordered_units, received_units, unit_price_cents)):
        raise ValueError("integer quantities and cents required")
    if ordered_units <= 0 or received_units < 0 or unit_price_cents < 0:
        raise ValueError("invalid quantity or price")
    if received_units >= ordered_units:
        raise ValueError("no shortage")
    missing = ordered_units - received_units
    return CreditDraft(venue_id, po_id, sku, missing, missing * unit_price_cents)


if __name__ == "__main__":
    import unittest

    class Tests(unittest.TestCase):
        def setUp(self):
            self.args = ("synthetic-a", "synthetic-a", "synthetic-a",
                         "PO-FAKE-1", "SYN-MILK", 10, 7, 199)

        def test_shortage(self):
            result = draft_credit(*self.args)
            self.assertEqual((result.missing_units, result.requested_cents, result.status),
                             (3, 597, "human_review_required"))

        def test_tenant(self):
            for index in (1, 2):
                args = list(self.args)
                args[index] = "synthetic-b"
                with self.assertRaises(ValueError):
                    draft_credit(*args)

        def test_no_shortage(self):
            for received in (10, 11):
                args = list(self.args)
                args[6] = received
                with self.assertRaises(ValueError):
                    draft_credit(*args)

        def test_invalid(self):
            for index, value in ((5, True), (6, -1), (7, 1.5), (4, " ")):
                args = list(self.args)
                args[index] = value
                with self.assertRaises(ValueError):
                    draft_credit(*args)

    unittest.main(verbosity=2)
