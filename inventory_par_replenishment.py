"""Offline, venue-scoped replenishment suggestions; never creates purchase orders.

Quantities are nonnegative integer base units defined by a trusted inventory SKU.
This module does not infer units, supplier availability, or purchasing authority.
"""


def suggest_replenishment(*, venue_id, sku_venue_id, on_hand, reserved,
                          par_level, target_level, pack_size=1):
    """Calculate an advisory pack-rounded replenishment quantity.

    A stock shortage never authorizes procurement. Negative available stock is
    retained for planning; it is not silently clipped to zero.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue_id required')
    if venue_id != sku_venue_id:
        raise PermissionError('SKU does not belong to requested venue')
    quantities = (on_hand, reserved, par_level, target_level, pack_size)
    if any(type(q) is not int or q < 0 for q in quantities) or pack_size == 0:
        raise ValueError('quantities must be nonnegative integers; pack_size > 0')
    if target_level < par_level:
        raise ValueError('target_level must be at least par_level')
    available = on_hand - reserved
    below_par = available < par_level
    deficit = max(0, target_level - available) if below_par else 0
    suggested = ((deficit + pack_size - 1) // pack_size) * pack_size
    return {'venue_id': venue_id, 'available_units': available,
            'below_par': below_par, 'suggested_units': suggested,
            'suggested_packs': suggested // pack_size,
            'status': 'review_suggestion' if below_par else 'no_action',
            'purchase_order_created': False}
