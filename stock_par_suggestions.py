"""Offline synthetic par-level replenishment calculations; no purchasing actions."""


def suggest_replenishment(*, on_hand_milliunits, reserved_milliunits, par_milliunits,
                          incoming_milliunits=0):
    """Return nonnegative suggested replenishment in integer milliunits.

    Reserved stock is unavailable; confirmed incoming stock reduces the suggestion.
    No automatic order, supplier contact, or product-specific safety threshold.
    """
    values = (on_hand_milliunits, reserved_milliunits, par_milliunits, incoming_milliunits)
    if any(type(value) is not int or value < 0 or value > 1_000_000_000_000
           for value in values):
        raise ValueError('Stock amounts must be nonnegative bounded integer milliunits')
    if reserved_milliunits > on_hand_milliunits:
        raise ValueError('Reserved stock cannot exceed on-hand stock')
    projected = on_hand_milliunits - reserved_milliunits + incoming_milliunits
    return max(0, par_milliunits - projected)
