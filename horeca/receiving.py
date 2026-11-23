"""Offline purchase-requisition delivery reconciliation; no inventory mutation."""
from dataclasses import dataclass
from horeca.purchasing import Requisition, Status


@dataclass(frozen=True)
class ReceiptVariance:
    requisition_id: str
    venue_id: str
    expected_units: int
    accepted_units: int
    rejected_units: int
    missing_units: int
    excess_units: int
    accepted_value_cents: int
    discrepancy: bool


def reconcile_delivery(req: Requisition, *, venue_id: str, actor_role: str,
                       delivered_units: int, rejected_units: int = 0) -> ReceiptVariance:
    """Compute an immutable review record, not a stock posting or supplier credit.

    Any shortfall, excess, or rejected units require human reconciliation.
    """
    if venue_id != req.venue_id:
        raise PermissionError('wrong venue')
    if actor_role not in ('receiver', 'manager', 'owner'):
        raise PermissionError('receiving permission required')
    if req.status != Status.APPROVED:
        raise ValueError('approved requisition required')
    if (type(delivered_units) is not int or type(rejected_units) is not int
            or delivered_units < 0 or rejected_units < 0
            or rejected_units > delivered_units):
        raise ValueError('invalid delivered/rejected quantities')
    accepted = delivered_units - rejected_units
    return ReceiptVariance(
        requisition_id=req.id, venue_id=req.venue_id,
        expected_units=req.quantity, accepted_units=accepted,
        rejected_units=rejected_units,
        missing_units=max(0, req.quantity - accepted),
        excess_units=max(0, accepted - req.quantity),
        accepted_value_cents=accepted * req.unit_price_cents,
        discrepancy=(accepted != req.quantity or rejected_units > 0),
    )
