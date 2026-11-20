"""Offline waste-event validation preview; never posts a stock-ledger event.

Caller-supplied venue and SKU ownership must be verified by trusted storage in
an authenticated service before this preview can become a write operation.
"""

MAX_UNITS = 1_000_000_000
REASONS = frozenset({'spoilage', 'damage', 'preparation_loss', 'expired', 'other'})


def preview_waste(*, venue_id, sku_venue_id, ledger_units, waste_units, unit,
                  reason, note=None):
    """Validate a proposed loss and return a review-only, non-mutating summary."""
    if type(venue_id) is not str or not venue_id.strip():
        raise ValueError('venue_id required')
    if venue_id != sku_venue_id:
        raise PermissionError('SKU venue mismatch')
    if type(unit) is not str or unit not in ('g', 'ml', 'each'):
        raise ValueError('unsupported unit')
    for name, value in (('ledger_units', ledger_units), ('waste_units', waste_units)):
        if type(value) is not int or not 0 <= value <= MAX_UNITS:
            raise ValueError(f'{name} must be a bounded nonnegative integer')
    if waste_units == 0 or waste_units > ledger_units:
        raise ValueError('waste must be positive and cannot exceed recorded stock')
    if type(reason) is not str or reason not in REASONS:
        raise ValueError('approved waste reason required')
    if note is not None and (type(note) is not str or len(note) > 500):
        raise ValueError('note must be at most 500 characters')
    if reason == 'other' and (note is None or not note.strip()):
        raise ValueError('other reason requires an explanation')
    return {'venue_id': venue_id, 'unit': unit, 'reason': reason,
            'waste_units': waste_units, 'projected_units': ledger_units - waste_units,
            'requires_review': True, 'posted': False}
