"""Offline receiving acceptance: rejected units and suggested credit, never issued."""
from dataclasses import dataclass
import unittest

@dataclass(frozen=True)
class Acceptance:
    venue_id: str
    sku: str
    ordered_units: int
    delivered_units: int
    accepted_units: int
    unit_price_cents: int

def assess(line: Acceptance) -> dict:
    if not line.venue_id or not line.sku:
        raise ValueError("venue and SKU required")
    nums = (line.ordered_units, line.delivered_units, line.accepted_units, line.unit_price_cents)
    if any(type(n) is not int or n < 0 for n in nums):
        raise ValueError("nonnegative integer quantities and cents required")
    if line.accepted_units > line.delivered_units:
        raise ValueError("accepted cannot exceed delivered")
    if line.delivered_units > line.ordered_units:
        raise ValueError("overdelivery requires separate review")
    short = line.ordered_units - line.delivered_units
    rejected = line.delivered_units - line.accepted_units
    return {"venue_id": line.venue_id, "sku": line.sku,
            "short_units": short, "rejected_units": rejected,
            "accepted_value_cents": line.accepted_units * line.unit_price_cents,
            "suggested_credit_cents": (short + rejected) * line.unit_price_cents,
            "status": "review_required" if short or rejected else "matched_unposted"}

class Tests(unittest.TestCase):
    def test_match(self):
        self.assertEqual(assess(Acceptance("fictional-a", "SYN-1", 10, 10, 10, 225))["status"], "matched_unposted")
    def test_rejected_and_short(self):
        r = assess(Acceptance("fictional-a", "SYN-1", 10, 8, 6, 225))
        self.assertEqual((r["short_units"], r["rejected_units"], r["accepted_value_cents"], r["suggested_credit_cents"]), (2, 2, 1350, 900))
    def test_invalid(self):
        for a in ((10, 11, 11, 225), (10, 5, 6, 225), (10, -1, 0, 225), (10, 10, 10, True)):
            with self.subTest(a=a), self.assertRaises(ValueError):
                assess(Acceptance("fictional-a", "SYN-1", *a))
    def test_missing_venue(self):
        with self.assertRaises(ValueError):
            assess(Acceptance("", "SYN-1", 10, 10, 10, 225))

if __name__ == "__main__":
    unittest.main()
