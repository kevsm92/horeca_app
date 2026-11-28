"""Synthetic partial-delivery acceptance guard; no stock or supplier side effects."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Receipt:
    venue_id: str
    order_id: str
    sku: str
    receipt_id: str
    accepted_units: int


def outstanding(venue_id: str, order_id: str, sku: str, ordered_units: int,
                receipts: tuple[Receipt, ...]) -> int:
    """Reject duplicate receipts and cross-tenant data before summing accepted units."""
    if not all(type(x) is str and x.strip() for x in (venue_id, order_id, sku)):
        raise ValueError('missing purchase identity')
    if type(ordered_units) is not int or ordered_units <= 0:
        raise ValueError('ordered_units must be positive integer')
    seen = set()
    accepted = 0
    for receipt in receipts:
        if not isinstance(receipt, Receipt) or (receipt.venue_id, receipt.order_id, receipt.sku) != (venue_id, order_id, sku):
            raise ValueError('receipt scope mismatch')
        if not isinstance(receipt.receipt_id, str) or not receipt.receipt_id.strip() or receipt.receipt_id in seen:
            raise ValueError('duplicate or missing receipt id')
        if type(receipt.accepted_units) is not int or receipt.accepted_units < 0:
            raise ValueError('invalid accepted units')
        seen.add(receipt.receipt_id)
        accepted += receipt.accepted_units
        if accepted > ordered_units:
            raise ValueError('accepted units exceed ordered quantity')
    return ordered_units - accepted


if __name__ == '__main__':
    import unittest

    class Tests(unittest.TestCase):
        def setUp(self):
            self.a = Receipt('fictional-a', 'PO-1', 'SKU-1', 'R-1', 3)

        def test_partial(self):
            self.assertEqual(outstanding('fictional-a', 'PO-1', 'SKU-1', 10, (self.a,)), 7)

        def test_duplicate(self):
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                outstanding('fictional-a', 'PO-1', 'SKU-1', 10, (self.a, self.a))

        def test_overaccept(self):
            with self.assertRaisesRegex(ValueError, 'exceed'):
                outstanding('fictional-a', 'PO-1', 'SKU-1', 3, (self.a, Receipt('fictional-a','PO-1','SKU-1','R-2',1)))

        def test_tenant(self):
            with self.assertRaisesRegex(ValueError, 'scope'):
                outstanding('fictional-b', 'PO-1', 'SKU-1', 10, (self.a,))

        def test_negative_and_bool(self):
            for qty in (-1, True):
                with self.assertRaises(ValueError):
                    outstanding('fictional-a','PO-1','SKU-1',10,(Receipt('fictional-a','PO-1','SKU-1','R-1',qty),))

    unittest.main(verbosity=2)
