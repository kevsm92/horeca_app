"""Synthetic offline three-way invoice line matching, no approvals or payment."""
from dataclasses import dataclass


@dataclass(frozen=True)
class InvoiceMatch:
    sku: str
    expected_cents: int
    invoiced_cents: int
    variance_cents: int
    status: str


def match_invoice(venue_id: str, po_venue: str, receipt_venue: str, invoice_venue: str,
                  sku: str, ordered_units: int, received_units: int,
                  invoiced_units: int, po_unit_cents: int, invoice_unit_cents: int) -> InvoiceMatch:
    if not venue_id or any(v != venue_id for v in (po_venue, receipt_venue, invoice_venue)):
        raise PermissionError('venue mismatch')
    if not sku or any(type(n) is not int or n < 0 for n in (
        ordered_units, received_units, invoiced_units, po_unit_cents, invoice_unit_cents)):
        raise ValueError('invalid invoice matching input')
    expected = received_units * po_unit_cents
    actual = invoiced_units * invoice_unit_cents
    matched = (ordered_units == received_units == invoiced_units and po_unit_cents == invoice_unit_cents)
    return InvoiceMatch(sku, expected, actual, actual - expected,
                        'matched' if matched else 'review_required')
