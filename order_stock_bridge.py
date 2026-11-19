"""Offline adapter joining a trusted order snapshot to the idempotent stock ledger.

Not an HTTP handler. The caller must authenticate, derive venue from server session,
verify immutable order lines and authorize the finalized order transition.
"""
from prototypes.stock_event import plan_deductions
from order_stock_event import record_order_consumption


def consume_finalized_order(connection, *, venue_id, order, recipes):
    """Deduct once for a server-verified final order; reject non-final states.

    order is a trusted snapshot with keys id, venue_id, status, lines.
    Only a finalized, non-voided snapshot may be passed; never accept raw POS input.
    """
    if not isinstance(venue_id, str) or not venue_id:
        raise ValueError('Authenticated venue required')
    if not isinstance(order, dict) or order.get('venue_id') != venue_id:
        raise ValueError('Order venue mismatch')
    if order.get('status') != 'finalized':
        raise ValueError('Order is not finalized')
    order_id = order.get('id')
    event_id, deductions = plan_deductions(order_id, order.get('lines'), recipes)
    ingredients = {d.ingredient_id: d.quantity_milliunits for d in deductions}
    return record_order_consumption(connection, venue_id=venue_id, event_id=event_id,
                                    order_id=order_id, ingredients=ingredients)
