"""Atomic venue-scoped physical table capacity adjustment (offline SQLite only).

Authorization of the venue is the caller's responsibility. Capacity is physical
seat inventory, not a floor-plan pixel dimension.
"""


def set_table_capacity(db, venue_id, table_id, capacity):
    """Set a physical table's seat count; reject unknown table or occupied shrink.

    Relies on tables_foundation's database trigger for concurrent occupancy checks.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('nonempty venue_id required')
    if not isinstance(table_id, str) or not table_id.strip():
        raise ValueError('nonempty table_id required')
    if type(capacity) is not int or not 1 <= capacity <= 100:
        raise ValueError('capacity must be an integer from 1 to 100')
    with db:
        result = db.execute(
            'UPDATE physical_tables SET capacity=? WHERE venue_id=? AND table_id=?',
            (capacity, venue_id, table_id),
        )
        if result.rowcount != 1:
            raise ValueError('physical table not found in venue')
