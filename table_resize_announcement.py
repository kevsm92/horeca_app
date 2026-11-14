"""Pure accessibility announcement formatter for a confirmed table resize.

Only call after a successful authorized, venue-scoped transaction. Never announce
optimistic edits as saved. No customer or staff data is accepted.
"""


def saved_resize_announcement(table_label, width_cm, depth_cm, seats, revision):
    """Return a screen-reader status message from validated committed values."""
    if not isinstance(table_label, str) or not (1 <= len(table_label) <= 40):
        raise ValueError('invalid table label')
    if any(ord(c) < 32 or ord(c) == 127 for c in table_label):
        raise ValueError('control character in table label')
    from decimal import Decimal, InvalidOperation
    values = []
    for value in (width_cm, depth_cm):
        if not isinstance(value, str):
            raise ValueError('normalized dimension string required')
        try:
            d = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError('invalid dimension') from exc
        if not d.is_finite() or not 30 <= d <= 500 or d % Decimal('0.5'):
            raise ValueError('invalid dimension')
        values.append(f'{d:.1f}')
    if type(seats) is not int or not 1 <= seats <= 100:
        raise ValueError('invalid seats')
    if type(revision) is not int or revision < 1:
        raise ValueError('invalid committed revision')
    return (f'Table {table_label}: saved width {values[0]} cm, depth {values[1]} cm, '
            f'{seats} seats. Revision {revision}.')
