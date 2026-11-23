"""Offline three-way match hold preview. Never posts stock, invoices or credits."""
from dataclasses import dataclass


@dataclass(frozen=True)
class MatchHold:
    venue_id: str
    po_id: str
    sku: str
    accepted_units: int
    payable_ceiling_cents: int
    reasons: tuple[str, ...]
    status: str = "human_review_required"
    posted: bool = False


def preview_match_hold(*, venue_id: str, po_id: str, sku: str,
                       ordered_units: int, delivered_units: int,
                       quarantined_units: int, rejected_units: int,
                       invoiced_units: int, agreed_unit_cents: int,
                       invoiced_unit_cents: int) -> MatchHold:
    """Only accepted, ordered units enter the provisional payable ceiling.

    This is a conservative review preview, not approval of any payable amount.
    """
    if any(type(v) is not str or not v.strip() for v in (venue_id, po_id, sku)):
        raise ValueError("missing venue, PO or SKU")
    numbers = (ordered_units, delivered_units, quarantined_units, rejected_units,
               invoiced_units, agreed_unit_cents, invoiced_unit_cents)
    if any(type(v) is not int or v < 0 for v in numbers) or agreed_unit_cents == 0:
        raise ValueError("invalid quantities or prices")
    if quarantined_units + rejected_units > delivered_units:
        raise ValueError("condition quantities exceed delivery")
    accepted = delivered_units - quarantined_units - rejected_units
    reasons = []
    if quarantined_units:
        reasons.append("quarantined_units_require_review")
    if rejected_units:
        reasons.append("rejected_units_excluded")
    if accepted > ordered_units:
        reasons.append("accepted_exceeds_ordered")
    if invoiced_units != accepted:
        reasons.append("invoice_quantity_differs_from_accepted")
    if invoiced_unit_cents != agreed_unit_cents:
        reasons.append("invoice_price_differs_from_po")
    if not reasons:
        reasons.append("manual_three_way_signoff_required")
    ceiling = min(ordered_units, accepted, invoiced_units) * min(agreed_unit_cents, invoiced_unit_cents)
    return MatchHold(venue_id, po_id, sku, accepted, ceiling, tuple(reasons))
