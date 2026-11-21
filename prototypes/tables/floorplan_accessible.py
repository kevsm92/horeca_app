"""Offline read-only accessible floor-plan projection. Synthetic data only.

Caller authorizes venue before obtaining preview; no seating mutation or saved geometry.
"""
from html import escape


def render_floorplan(preview):
    if not isinstance(preview, dict) or preview.get('layout') != 'provisional-grid':
        raise ValueError('provisional-grid preview required')
    tiles = preview.get('tiles')
    if not isinstance(tiles, list):
        raise ValueError('tiles must be a list')
    seen_ids, seen_cells, items = set(), set(), []
    for tile in tiles:
        if not isinstance(tile, dict):
            raise ValueError('invalid tile')
        table_id = tile.get('table_id')
        capacity, guests = tile.get('capacity'), tile.get('guest_count')
        status, session_id = tile.get('status'), tile.get('session_id')
        x, y = tile.get('x'), tile.get('y')
        if not isinstance(table_id, str) or not table_id.strip() or table_id in seen_ids:
            raise ValueError('invalid or duplicate table')
        if type(x) is not int or type(y) is not int or x < 0 or y < 0 or (x, y) in seen_cells:
            raise ValueError('invalid or duplicate grid cell')
        if type(capacity) is not int or capacity < 1 or type(guests) is not int or not 0 <= guests <= capacity:
            raise ValueError('invalid capacity or guests')
        if status not in ('available', 'occupied') or (status == 'occupied') != (guests > 0):
            raise ValueError('inconsistent occupancy')
        if (status == 'occupied') != (isinstance(session_id, str) and bool(session_id.strip())):
            raise ValueError('inconsistent seating session')
        if tile.get('can_seat') is not (status == 'available') or tile.get('position_saved') is not False:
            raise ValueError('inconsistent preview metadata')
        seen_ids.add(table_id)
        seen_cells.add((x, y))
        label = escape(table_id, quote=True)
        items.append(f'<li>Table {label}: {status}; {guests} of {capacity} seats; '
                     f'grid column {x + 1}, row {y + 1}</li>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<title>Tables floor plan — offline preview</title><main>'
            '<nav aria-label="Primary"><span aria-current="page">Tables</span></nav>'
            '<h1>Tables — provisional floor plan</h1>'
            '<p>Read-only synthetic preview. Positions are not saved. Seating is disabled.</p>'
            '<ol aria-label="Physical table grid">' + ''.join(items) + '</ol></main></html>')
