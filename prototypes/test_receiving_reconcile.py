import unittest
from receiving_reconcile import OrderedLine, DeliveredLine, reconcile

class ReconcileTests(unittest.TestCase):
    def test_short_excess_and_unexpected(self):
        rows = reconcile([OrderedLine("A", 10, 125), OrderedLine("B", 2, 500)],
                         [DeliveredLine("A", 7), DeliveredLine("B", 3), DeliveredLine("C", 1)])
        self.assertEqual([x["status"] for x in rows], ["short", "excess", "unexpected_sku"])
        self.assertEqual([x["variance_value_cents"] for x in rows], [-375, 500, None])

    def test_missing(self):
        self.assertEqual(reconcile([OrderedLine("A", 1, 10)], [])[0]["status"], "short")

    def test_invalid(self):
        for ordered, delivered in [
            ([OrderedLine("A", 1, 1)] * 2, []),
            ([], [DeliveredLine("A", -1)]),
            ([OrderedLine("A", True, 1)], [])]:
            with self.assertRaises(ValueError):
                reconcile(ordered, delivered)

    def test_matched(self):
        self.assertEqual(reconcile([OrderedLine("A", 1, 5)], [DeliveredLine("A", 1)])[0]["status"], "matched")

if __name__ == "__main__":
    unittest.main()
