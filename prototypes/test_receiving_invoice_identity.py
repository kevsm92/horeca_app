"""Synthetic receipt-to-invoice identity tests."""
import unittest
from receiving_invoice_batch import InvoiceLine
from receiving_invoice_identity import ReceiptReference, reconcile_for_receipt


class ReceiptIdentityTests(unittest.TestCase):
    def setUp(self):
        self.args = dict(venue_id="fictional-venue-a", po_venue_id="fictional-venue-a",
                         invoice_venue_id="fictional-venue-a", purchase_order_id="PO-FAKE-1",
                         receipt=ReceiptReference("fictional-venue-a", "PO-FAKE-1", "REC-FAKE-1", "accepted"),
                         accepted_receipt_lines=[InvoiceLine("SYN-FLOUR", 3, 200)],
                         invoice_lines=[InvoiceLine("SYN-FLOUR", 3, 200)])

    def test_matching_accepted_receipt(self):
        result = reconcile_for_receipt(**self.args)
        self.assertEqual((result.status, result.expected_cents), ("matched", 600))

    def test_receipt_from_another_venue_rejected(self):
        self.args["receipt"] = ReceiptReference("fictional-venue-b", "PO-FAKE-1", "REC-FAKE-1", "accepted")
        with self.assertRaises(PermissionError):
            reconcile_for_receipt(**self.args)

    def test_receipt_from_another_po_rejected(self):
        self.args["receipt"] = ReceiptReference("fictional-venue-a", "PO-FAKE-2", "REC-FAKE-1", "accepted")
        with self.assertRaises(ValueError):
            reconcile_for_receipt(**self.args)

    def test_unaccepted_receipt_rejected(self):
        for status in ("draft", "disputed", "cancelled", ""):
            with self.subTest(status=status):
                self.args["receipt"] = ReceiptReference("fictional-venue-a", "PO-FAKE-1", "REC-FAKE-1", status)
                with self.assertRaises(ValueError):
                    reconcile_for_receipt(**self.args)

    def test_missing_receipt_id_rejected(self):
        self.args["receipt"] = ReceiptReference("fictional-venue-a", "PO-FAKE-1", "", "accepted")
        with self.assertRaises(ValueError):
            reconcile_for_receipt(**self.args)

    def test_invoice_cross_venue_rejected(self):
        self.args["invoice_venue_id"] = "fictional-venue-b"
        with self.assertRaises(PermissionError):
            reconcile_for_receipt(**self.args)

    def test_non_reference_rejected(self):
        self.args["receipt"] = {"receipt_id": "REC-FAKE-1"}
        with self.assertRaises(ValueError):
            reconcile_for_receipt(**self.args)


if __name__ == "__main__":
    unittest.main()
