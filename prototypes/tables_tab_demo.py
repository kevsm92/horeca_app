"""Offline synthetic Tables tab HTML prototype; no backend or authentication."""
from html import escape


def render_tables_tab(rows):
    """Render an accessible read-only table list from trusted occupancy tuples."""
    allowed = {'available', 'occupied', 'unavailable'}
    items = []
    seen = set()
    for table_id, capacity, status, guests, _session_id in rows:
        if not isinstance(table_id, str) or not table_id or table_id in seen:
            raise ValueError('invalid or duplicate physical table')
        seen.add(table_id)
        if status not in allowed or type(capacity) is not int or capacity < 1:
            raise ValueError('invalid table projection')
        if type(guests) is not int or guests < 0 or guests > capacity:
            raise ValueError('invalid guest count')
        if (status == 'occupied') != (guests > 0):
            raise ValueError('inconsistent occupancy')
        label = escape(table_id, quote=True)
        items.append(f'<li><strong>{label}</strong> — {escape(status)}; '
                     f'{guests} of {capacity} seats occupied</li>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<title>Tables — synthetic offline prototype</title>'
            '<main><nav aria-label="Primary"><a href="#tables" aria-current="page">Tables</a></nav>'
            '<h1 id="tables">Tables</h1><p>Offline fictional data; read-only. '
            'No seating changes are available.</p><ul aria-label="Physical tables">'
            + ''.join(items) + '</ul></main></html>')


if __name__ == '__main__':
    import unittest

    class TablesTabTests(unittest.TestCase):
        def test_accessible_labels(self):
            page = render_tables_tab([('T1', 4, 'occupied', 2, 's1'),
                                      ('T2', 2, 'available', 0, None)])
            self.assertIn('aria-current="page"', page)
            self.assertIn('2 of 4 seats occupied', page)
            self.assertIn('available', page)

        def test_escapes_table_names(self):
            page = render_tables_tab([('<script>', 2, 'available', 0, None)])
            self.assertNotIn('<script>', page)
            self.assertIn('&lt;script&gt;', page)

        def test_fail_closed(self):
            bad = [[('T1', 2, 'occupied', 0, None)],
                   [('T1', 2, 'available', 1, None)],
                   [('T1', 2, 'occupied', 3, 's')],
                   [('T1', 2, 'available', 0, None), ('T1', 2, 'available', 0, None)]]
            for rows in bad:
                with self.subTest(rows=rows), self.assertRaises(ValueError):
                    render_tables_tab(rows)

    unittest.main()
