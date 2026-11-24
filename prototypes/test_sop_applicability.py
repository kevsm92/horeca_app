import unittest
from sop_applicability import SOPScope, applicable


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.scope = SOPScope('fictional-venue-a', 2, frozenset({'cook'}),
                              frozenset({'kitchen'}), frozenset({'fridge-1'}))

    def test_matching_scope(self):
        self.assertTrue(applicable(self.scope, venue_id='fictional-venue-a', role='cook', station='kitchen', equipment_id='fridge-1'))

    def test_cross_venue_denied(self):
        self.assertFalse(applicable(self.scope, venue_id='fictional-venue-b', role='cook', station='kitchen', equipment_id='fridge-1'))

    def test_all_dimensions_required(self):
        for kwargs in ({'role': 'server'}, {'station': 'bar'}, {'equipment_id': 'fridge-2'}, {'equipment_id': None}):
            params = dict(venue_id='fictional-venue-a', role='cook', station='kitchen', equipment_id='fridge-1')
            params.update(kwargs)
            self.assertFalse(applicable(self.scope, **params))

    def test_venue_wide_scope(self):
        wide = SOPScope('fictional-venue-a', 1, frozenset(), frozenset(), frozenset())
        self.assertTrue(applicable(wide, venue_id='fictional-venue-a', role='server', station='bar'))

    def test_invalid_scope_and_missing_context(self):
        with self.assertRaises(ValueError):
            applicable(SOPScope('fictional-venue-a', 0, frozenset(), frozenset(), frozenset()), venue_id='fictional-venue-a', role='cook', station='kitchen')
        with self.assertRaises(ValueError):
            applicable(self.scope, venue_id='fictional-venue-a', role='', station='kitchen')


if __name__ == '__main__':
    unittest.main()
