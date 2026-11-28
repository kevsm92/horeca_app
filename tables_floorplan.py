"""Deterministic read-only floor-plan projection; no browser or persistence.

The venue must already be authorized by the caller. Coordinates are provisional
layout hints, not saved positions or a claim about physical geometry.
"""
from tables_navigation import tables_tab_model


def floorplan_preview(db, venue_id, columns=4):
    """Return venue-isolated table tiles in stable grid order.

    Reject invalid layout configuration; preserve occupancy and Seat eligibility
    from the underlying Tables-tab model rather than recomputing either.
    """
    if type(columns) is not int or not 1 <= columns <= 12:
        raise ValueError('columns must be an integer from 1 to 12')
    model = tables_tab_model(db, venue_id)
    tiles = []
    for index, row in enumerate(model['tables']):
        tiles.append({**row, 'x': index % columns, 'y': index // columns,
                      'position_saved': False})
    return {'tab': 'Tables', 'venue_id': venue_id,
            'layout': 'provisional-grid', 'tiles': tiles}
