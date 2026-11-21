"""Offline, read-only stock count variance preview (synthetic data only).

All quantities are whole ingredient ledger units (g, ml, or each). A count
preview is not an authorized stock adjustment or evidence of physical checking.
"""

MAX_UNITS = 1_000_000_000


def preview_count(*, ledger_units: int, counted_units: int, unit: str) -> dict:
    """Return signed variance without mutating inventory or posting events."""
    if unit not in ('g', 'ml', 'each') or type(unit) is not str:
        raise ValueError('unsupported ingredient unit')
    for name, value in (('ledger_units', ledger_units), ('counted_units', counted_units)):
        if type(value) is not int or not 0 <= value <= MAX_UNITS:
            raise ValueError(f'{name} must be a bounded nonnegative integer')
    variance = counted_units - ledger_units
    return {'unit': unit, 'ledger_units': ledger_units,
            'counted_units': counted_units, 'variance_units': variance,
            'requires_review': variance != 0, 'posted': False}
