"""Venue-scoped availability projection; offline SQLite and synthetic data only.

Caller must authorize venue_id; this is not an authentication boundary.
"""
from tables_occupancy import occupancy_for_venue


def list_table_availability(db, venue_id):
    """Return (table_id, capacity, guests, spare_seats, vacant|occupied).

    Spare seats never imply a second seating is allowed. Fail closed on corrupt
    active sessions rather than presenting a table as bookable.
    """
    return [(table_id, capacity, guests, capacity - guests,
             'occupied' if status == 'occupied' else 'vacant')
            for table_id, capacity, status, guests, _ in occupancy_for_venue(db, venue_id)]
