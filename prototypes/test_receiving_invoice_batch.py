"""Focused tests for offline invoice batch reconciliation."""
import unittest
from receiving_invoice_batch import InvoiceLine, reconcile_invoice_batch


class InvoiceBatchTests(unittest.TestCase):
    def setUp(self):
        self.args = dict(venue_id="synthetic-a", po_venue_id="synthetic-a",
                         receipt_venue_id="synthetic-a", invoice_venue_id="synthetic-a",
                         purchase_order_id="PO-FAKE-9",
                         accepted_receipt_lines=[InvoiceLine("SYN-A", 3, 150), InvoiceLine("SYN-B", 2, 200)],
                         invoice_lines=[InvoiceLine("SYN-A", 3, 150), InvoiceLine("SYN-B", 2, 200)])

    def test_exact_batch(self):
        result = reconcile_invoice_batch(**self.args)
        self.assertEqual((result.status, result.expected_cents, result.invoiced_cents), ("matched", 850, 850))
        self.assertEqual([x.status for x in result.lines], ["matched", "matched"])

    def test_missing_and_extra_invoice_lines(self):
        self.args["invoice_lines"] = [InvoiceLine("SYN-A", 3, 150), InvoiceLine("SYN-X", 1, 50)]
        result = reconcile_invoice_batch(**self.args)
        self.assertEqual([x.status for x in result.lines], ["matched", "missing_invoice_line", "unexpected_invoice_line"])
        self.assertEqual(result.status, "human_review_required")
        self.assertEqual((result.expected_cents, result.invoiced_cents), (850, 500))

    def test_offsetting_variances_still_require_review(self):
        self.args["invoice_lines"] = [InvoiceLine("SYN-A", 2, 150), InvoiceLine("SYN-B", 2, 275)]
        result = reconcile_invoice_batch(**self.args)
        self.assertEqual(result.expected_cents, result.invoiced_cents)
        self.assertEqual(result.status, "human_review_required")

    def test_cross_venue_denied(self):
        self.args["invoice_venue_id"] = "synthetic-b"
        with self.assertRaises(PermissionError):
            reconcile_invoice_batch(**self.args)

    def test_duplicate_sku_rejected(self):
        self.args["invoice_lines"].append(InvoiceLine("SYN-A", 1, 150))
        with self.assertRaises(ValueError):
            reconcile_invoice_batch(**self.args)

    def test_boolean_float_negative_and_empty_rejected(self):
        for invalid in (True, 1.2, -1):
            self.args["invoice_lines"] = [InvoiceLine("SYN-A", invalid, 150)]
            with self.assertRaises(ValueError):
                reconcile_invoice_batch(**self.args)
        self.args["invoice_lines"] = []
        self.args["accepted_receipt_lines"] = []
        with self.assertRaises(ValueError):
            reconcile_invoice_batch(**self.args)

    def test_price_variance_and_deterministic_order(self):
        self.args["invoice_lines"] = [InvoiceLine("SYN-B", 2, 201), InvoiceLine("SYN-A", 3, 150)]
        result = reconcile_invoice_batch(**self.args)
        self.assertEqual([x.sku for x in result.lines], ["SYN-A", "SYN-B"])
        self.assertEqual(result.lines[1].variance_cents, 2)
        self.assertEqual(result.status, "human_review_required")


if __name__ == "__main__":
    unittest.main()
