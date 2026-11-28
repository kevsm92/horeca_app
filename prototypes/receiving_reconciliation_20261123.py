"""Offline synthetic goods-receiving reconciliation prototype (no orders or payments)."""
from dataclasses import dataclass
from unittest import TestCase, main


@dataclass(frozen=True)
class PurchaseLine:
    venue_id: str
    sku: str
    ordered_units: int
    unit_price_cents: int


@dataclass(frozen=True)
class DeliveryLine:
    venue_id: str
    sku: str
    delivered_units: int
    rejected_units: int = 0


@dataclass(frozen=True)
class InvoiceLine:
    venue_id: str
    sku: str
    billed_units: int
    unit_price_cents: int


def reconcile(purchase: PurchaseLine, delivery: DeliveryLine, invoice: InvoiceLine) -> dict:
    """Compare one PO, delivery and invoice line; never approve or post a transaction."""
    if not purchase.venue_id or not purchase.sku:
        raise ValueError('venue and SKU required')
    if any((x.venue_id, x.sku) != (purchase.venue_id, purchase.sku)
           for x in (delivery, invoice)):
        raise ValueError('venue/SKU mismatch')
    values = (purchase.ordered_units, purchase.unit_price_cents,
              delivery.delivered_units, delivery.rejected_units,
              invoice.billed_units, invoice.unit_price_cents)
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError('quantities and prices must be nonnegative integers')
    if purchase.ordered_units == 0 or purchase.unit_price_cents == 0:
        raise ValueError('PO must have positive quantity and price')
    if delivery.rejected_units > delivery.delivered_units:
        raise ValueError('rejected quantity exceeds delivered quantity')
    accepted = delivery.delivered_units - delivery.rejected_units
    reasons = []
    if accepted != purchase.ordered_units:
        reasons.append('accepted_quantity_differs_from_po')
    if delivery.rejected_units:
        reasons.append('rejected_goods_require_review')
    if invoice.billed_units != accepted:
        reasons.append('invoice_quantity_differs_from_accepted')
    if invoice.unit_price_cents != purchase.unit_price_cents:
        reasons.append('invoice_price_differs_from_po')
    return {
        'venue_id': purchase.venue_id, 'sku': purchase.sku,
        'accepted_units': accepted,
        'quantity_variance_units': accepted - purchase.ordered_units,
        'invoice_total_cents': invoice.billed_units * invoice.unit_price_cents,
        'expected_accepted_total_cents': accepted * purchase.unit_price_cents,
        'status': 'matched_for_manual_review' if not reasons else 'discrepancy',
        'reasons': tuple(reasons),
        'requires_human_approval': True,
    }


class ReconciliationTests(TestCase):
    def setUp(self):
        self.po = PurchaseLine('fictional-venue-a', 'SYN-MILK', 10, 250)

    def test_exact_match_still_requires_review(self):
        result = reconcile(self.po, DeliveryLine('fictional-venue-a', 'SYN-MILK', 10),
                           InvoiceLine('fictional-venue-a', 'SYN-MILK', 10, 250))
        self.assertEqual(result['status'], 'matched_for_manual_review')
        self.assertTrue(result['requires_human_approval'])
        self.assertEqual(result['invoice_total_cents'], 2500)

    def test_rejected_goods_and_overbilling(self):
        result = reconcile(self.po, DeliveryLine('fictional-venue-a', 'SYN-MILK', 10, 2),
                           InvoiceLine('fictional-venue-a', 'SYN-MILK', 10, 250))
        self.assertEqual(result['accepted_units'], 8)
        self.assertEqual(result['quantity_variance_units'], -2)
        self.assertIn('invoice_quantity_differs_from_accepted', result['reasons'])
        self.assertIn('rejected_goods_require_review', result['reasons'])

    def test_tenant_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            reconcile(self.po, DeliveryLine('fictional-venue-b', 'SYN-MILK', 10),
                      InvoiceLine('fictional-venue-a', 'SYN-MILK', 10, 250))

    def test_invalid_quantities_and_boolean_rejected(self):
        with self.assertRaises(ValueError):
            reconcile(self.po, DeliveryLine('fictional-venue-a', 'SYN-MILK', 1, 2),
                      InvoiceLine('fictional-venue-a', 'SYN-MILK', 1, 250))
        with self.assertRaises(ValueError):
            reconcile(self.po, DeliveryLine('fictional-venue-a', 'SYN-MILK', True),
                      InvoiceLine('fictional-venue-a', 'SYN-MILK', 1, 250))

    def test_price_discrepancy(self):
        result = reconcile(self.po, DeliveryLine('fictional-venue-a', 'SYN-MILK', 10),
                           InvoiceLine('fictional-venue-a', 'SYN-MILK', 10, 300))
        self.assertEqual(result['status'], 'discrepancy')
        self.assertIn('invoice_price_differs_from_po', result['reasons'])


if __name__ == '__main__':
    main()
