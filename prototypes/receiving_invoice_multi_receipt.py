"""Offline aggregation of multiple accepted receipts for one PO; no invoice posting."""
from collections import defaultdict
from dataclasses import dataclass
import sqlite3


@dataclass(frozen=True)
class AggregatedReceiptLine:
    sku: str
    accepted_units: int
    agreed_unit_cents: int


def accepted_po_receipt_lines(conn: sqlite3.Connection, *, venue_id: str,
                              purchase_order_id: str, receipt_ids: tuple[str, ...]):
    """Aggregate trusted accepted receipts, rejecting inconsistent PO prices.

    Callers must derive venue_id from authenticated server context, not request data.
    An empty or partial receipt selection is not proof of full PO invoicing.
    """
    if not isinstance(venue_id, str) or not venue_id.strip() or not isinstance(purchase_order_id, str) or not purchase_order_id.strip():
        raise ValueError('venue and purchase order required')
    if not isinstance(receipt_ids, (list, tuple)) or not receipt_ids or any(
            not isinstance(r, str) or not r.strip() for r in receipt_ids):
        raise ValueError('nonempty receipt identifiers required')
    if len(set(receipt_ids)) != len(receipt_ids):
        raise ValueError('duplicate receipt identifiers')
    po = conn.execute('SELECT 1 FROM receiving_purchase_orders WHERE venue_id=? AND purchase_order_id=?',
                      (venue_id, purchase_order_id)).fetchone()
    if po is None:
        raise ValueError('purchase order not found in venue')
    totals = defaultdict(int)
    prices = {}
    for receipt_id in receipt_ids:
        row = conn.execute('SELECT purchase_order_id, status FROM receiving_receipts WHERE venue_id=? AND receipt_id=?',
                           (venue_id, receipt_id)).fetchone()
        if row is None or row[0] != purchase_order_id or row[1] != 'accepted':
            raise ValueError('receipt missing, unaccepted, or belongs to another PO')
        lines = conn.execute('SELECT sku, accepted_units, agreed_unit_cents FROM receiving_receipt_lines '
                             'WHERE venue_id=? AND receipt_id=? ORDER BY sku', (venue_id, receipt_id)).fetchall()
        if not lines:
            raise ValueError('accepted receipt without lines')
        seen = set()
        for sku, units, cents in lines:
            if not isinstance(sku, str) or not sku.strip() or sku in seen or type(units) is not int or type(cents) is not int or units < 0 or cents < 0:
                raise ValueError('invalid stored receipt line')
            seen.add(sku)
            if sku in prices and prices[sku] != cents:
                raise ValueError('inconsistent agreed price across receipts requires human review')
            prices[sku] = cents
            totals[sku] += units
    return tuple(AggregatedReceiptLine(sku, totals[sku], prices[sku]) for sku in sorted(totals))
