"""Offline Tables-tab view model. Authorization of venue_id is caller's duty."""
from tables_occupancy import occupancy_for_venue


def tables_tab_model(db, venue_id):
    """Produce deterministic, read-only rows with a safe Seat action flag.

    Occupied tables are never offered for new seating, even with spare capacity.
    This model does not implement an authenticated UI or seat mutation.
    """
    rows = []
    for table_id, capacity, status, guests, session_id in occupancy_for_venue(db, venue_id):
        rows.append({
            'table_id': table_id,
            'capacity': capacity,
            'status': status,
            'guest_count': guests,
            'session_id': session_id,
            'can_seat': status == 'available',
            'label': f'Table {table_id}: {status}, {guests} of {capacity} seats',
        })
    return {'tab': 'Tables', 'venue_id': venue_id, 'tables': rows}
