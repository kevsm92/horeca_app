"""Synthetic, offline invoice batch reconciliation against accepted receipt lines.

No supplier transmission, accounting posting, approval, or payment is performed.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class InvoiceLine:
    sku: str
    units: int
    unit_cents: int


@dataclass(frozen=True)
class LineVariance:
    sku: str
    received_units: int
    invoiced_units: int
    expected_cents: int
    invoiced_cents: int
    variance_cents: int
    status: str


@dataclass(frozen=True)
class InvoiceBatchReview:
    venue_id: str
    purchase_order_id: str
    lines: tuple[LineVariance, ...]
    expected_cents: int
    invoiced_cents: int
    status: str = "human_review_required"


def _validate_lines(lines, label):
    if not isinstance(lines, (tuple, list)):
        raise ValueError(f"{label} must be a sequence")
    indexed = {}
    for line in lines:
        if not isinstance(line, InvoiceLine) or not isinstance(line.sku, str) or not line.sku.strip():
            raise ValueError(f"invalid {label} line")
        if type(line.units) is not int or type(line.unit_cents) is not int or line.units < 0 or line.unit_cents < 0:
            raise ValueError(f"invalid {label} quantity or cents")
        if line.sku in indexed:
            raise ValueError(f"duplicate SKU in {label}; aggregate explicitly before matching")
        indexed[line.sku] = line
    return indexed


def reconcile_invoice_batch(*, venue_id, po_venue_id, receipt_venue_id,
                            invoice_venue_id, purchase_order_id,
                            accepted_receipt_lines, invoice_lines):
    """Compare invoice lines with accepted receipts using integer EUR cents.

    Expected price is the PO-agreed unit price carried on accepted receipt lines.
    Missing/extra SKUs and quantity/price deviations always require human review.
    """
    if not all(isinstance(v, str) and v.strip() for v in (venue_id, po_venue_id,
            receipt_venue_id, invoice_venue_id, purchase_order_id)):
        raise ValueError("missing identity")
    if any(v != venue_id for v in (po_venue_id, receipt_venue_id, invoice_venue_id)):
        raise PermissionError("cross-venue invoice reconciliation denied")
    receipt = _validate_lines(accepted_receipt_lines, "receipt")
    invoice = _validate_lines(invoice_lines, "invoice")
    if not receipt and not invoice:
        raise ValueError("empty reconciliation")
    results = []
    for sku in sorted(set(receipt) | set(invoice)):
        r, i = receipt.get(sku), invoice.get(sku)
        expected = r.units * r.unit_cents if r else 0
        actual = i.units * i.unit_cents if i else 0
        status = ("matched" if r and i and r.units == i.units and r.unit_cents == i.unit_cents
                  else "missing_invoice_line" if not i else "unexpected_invoice_line" if not r
                  else "quantity_or_price_variance")
        results.append(LineVariance(sku, r.units if r else 0, i.units if i else 0,
                                    expected, actual, actual - expected, status))
    return InvoiceBatchReview(venue_id, purchase_order_id, tuple(results),
                              sum(x.expected_cents for x in results),
                              sum(x.invoiced_cents for x in results),
                              "matched" if all(x.status == "matched" for x in results)
                              else "human_review_required")
