"""Offline PO delivery-shortage review; no stock, invoice, or supplier side effects."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ShortageReview:
    venue_id: str
    po_id: str
    sku: str
    ordered_units: int
    previously_accepted_units: int
    newly_accepted_units: int
    outstanding_units: int
    outstanding_value_cents: int
    reasons: tuple[str, ...]
    status: str = "human_review_required"
    posted: bool = False


def preview_shortage(*, venue_id: str, po_id: str, sku: str,
                     ordered_units: int, previously_accepted_units: int,
                     delivered_units: int, quarantined_units: int,
                     rejected_units: int, agreed_unit_cents: int) -> ShortageReview:
    """Calculate outstanding ordered units across partial deliveries.

    Previously accepted units are trusted input from the same venue/PO/SKU;
    callers must resolve that identity from authorized storage, never client claims.
    Quarantined units remain outstanding pending a separately audited decision.
    """
    if any(type(s) is not str or not s.strip() for s in (venue_id, po_id, sku)):
        raise ValueError("missing scoped purchase identity")
    values = (ordered_units, previously_accepted_units, delivered_units,
              quarantined_units, rejected_units, agreed_unit_cents)
    if any(type(n) is not int or n < 0 for n in values) or agreed_unit_cents == 0:
        raise ValueError("invalid quantities or agreed price")
    if quarantined_units + rejected_units > delivered_units:
        raise ValueError("delivery condition counts exceed delivered units")
    newly_accepted = delivered_units - quarantined_units - rejected_units
    total_accepted = previously_accepted_units + newly_accepted
    if previously_accepted_units > ordered_units or total_accepted > ordered_units:
        raise ValueError("accepted quantity exceeds ordered quantity; review overdelivery separately")
    outstanding = ordered_units - total_accepted
    reasons = []
    if outstanding:
        reasons.append("ordered_units_outstanding")
    if quarantined_units:
        reasons.append("quarantined_units_not_accepted")
    if rejected_units:
        reasons.append("rejected_units_not_accepted")
    if not reasons:
        reasons.append("manual_receipt_signoff_required")
    return ShortageReview(venue_id, po_id, sku, ordered_units,
                          previously_accepted_units, newly_accepted,
                          outstanding, outstanding * agreed_unit_cents,
                          tuple(reasons))
