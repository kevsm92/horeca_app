"""Offline, read-only floor-plan renderer for an authorized synthetic projection."""
from html import escape
import unittest


def render_floorplan(preview):
    """Fail closed on inconsistent tiles; never imply positions were saved."""
    if preview.get('tab') != 'Tables' or preview.get('layout') != 'provisional-grid':
        raise ValueError('unsupported projection')
    tiles = preview.get('tiles')
    if not isinstance(tiles, list):
        raise ValueError('tiles must be a list')
    seen_ids, seen_cells, items = set(), set(), []
    for tile in tiles:
        table_id = tile.get('table_id')
        x, y = tile.get('x'), tile.get('y')
        status = tile.get('status')
        guests, capacity = tile.get('guest_count'), tile.get('capacity')
        if (not isinstance(table_id, str) or not table_id or table_id in seen_ids
                or type(x) is not int or type(y) is not int or x < 0 or y < 0
                or (x, y) in seen_cells or tile.get('position_saved') is not False
                or status not in ('available', 'occupied', 'unavailable')
                or type(guests) is not int or type(capacity) is not int
                or capacity < 1 or not 0 <= guests <= capacity
                or (status == 'occupied') != (guests > 0)
                or tile.get('can_seat') is not (status == 'available')):
            raise ValueError('inconsistent tile')
        seen_ids.add(table_id)
        seen_cells.add((x, y))
        items.append('<li><strong>' + escape(table_id, quote=True)
                     + '</strong>: ' + escape(status)
                     + f'; {guests} of {capacity} seats; provisional column {x + 1}, row {y + 1}</li>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<title>Tables floor plan — offline</title><main>'
            '<nav aria-label="Primary"><a href="#tables" aria-current="page">Tables</a></nav>'
            '<h1 id="tables">Tables floor plan</h1>'
            '<p>Read-only provisional layout. Positions are not saved. '
            'No seating or editing actions are available.</p>'
            '<ol aria-label="Physical tables in provisional grid">'
            + ''.join(items) + '</ol></main></html>')


class FloorplanHTMLTests(unittest.TestCase):
    def setUp(self):
        self.tile = {'table_id': '<T1>', 'x': 0, 'y': 0, 'status': 'occupied',
                     'guest_count': 2, 'capacity': 4, 'can_seat': False,
                     'position_saved': False}

    def preview(self, tiles):
        return {'tab': 'Tables', 'layout': 'provisional-grid', 'tiles': tiles}

    def test_accessible_read_only_and_escaped(self):
        page = render_floorplan(self.preview([self.tile]))
        self.assertIn('aria-label="Physical tables', page)
        self.assertIn('&lt;T1&gt;', page)
        self.assertNotIn('<T1>', page)
        self.assertIn('Positions are not saved', page)
        self.assertNotIn('<button', page)

    def test_rejects_invalid_tiles(self):
        for patch in ({'can_seat': True}, {'position_saved': True},
                      {'guest_count': 0}, {'x': -1}, {'capacity': True}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                render_floorplan(self.preview([{**self.tile, **patch}]))

    def test_rejects_duplicate_grid_cells(self):
        with self.assertRaises(ValueError):
            render_floorplan(self.preview([self.tile, {**self.tile, 'table_id': 'T2'}]))


if __name__ == '__main__':
    unittest.main()
