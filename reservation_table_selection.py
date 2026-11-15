"""Deterministic, offline table suggestion from a prevalidated availability snapshot.

A suggestion is NOT a reservation. The write transaction must independently
recheck venue, physical capacity, seating sessions, conflicts and turnover.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    venue_id: str
    table_id: str
    physical_seats: int


def suggest_table(venue_id: str, party_size: int, available_ids: tuple[str, ...],
                  inventory: tuple[Candidate, ...]) -> str | None:
    """Prefer smallest sufficient table, then stable ID; reject corrupt snapshots."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if type(party_size) is not int or party_size < 1:
        raise ValueError('positive integer party required')
    if not isinstance(available_ids, tuple) or not isinstance(inventory, tuple):
        raise ValueError('immutable snapshot tuples required')
    by_id = {}
    for row in inventory:
        if not isinstance(row, Candidate) or not row.table_id or not row.venue_id:
            raise ValueError('invalid inventory row')
        if type(row.physical_seats) is not int or row.physical_seats < 1:
            raise ValueError('invalid physical seats')
        if row.venue_id == venue_id:
            if row.table_id in by_id:
                raise ValueError('duplicate table ID in venue')
            by_id[row.table_id] = row
    if any(type(t) is not str or not t for t in available_ids):
        raise ValueError('invalid available ID')
    if len(set(available_ids)) != len(available_ids):
        raise ValueError('duplicate available IDs')
    if any(t not in by_id for t in available_ids):
        raise ValueError('unknown or cross-venue availability ID')
    eligible = (by_id[t] for t in available_ids if by_id[t].physical_seats >= party_size)
    chosen = min(eligible, key=lambda t: (t.physical_seats, t.table_id), default=None)
    return chosen.table_id if chosen else None


if __name__ == '__main__':
    import unittest

    class SelectionTests(unittest.TestCase):
        def setUp(self):
            self.rows = (Candidate('a', 'T8', 8), Candidate('a', 'T4B', 4),
                         Candidate('a', 'T4A', 4), Candidate('b', 'T2', 2))

        def test_least_waste_stable_tie(self):
            self.assertEqual(suggest_table('a', 3, ('T8', 'T4B', 'T4A'), self.rows), 'T4A')

        def test_empty_or_insufficient(self):
            self.assertIsNone(suggest_table('a', 9, ('T8',), self.rows))
            self.assertIsNone(suggest_table('a', 2, (), self.rows))

        def test_cross_venue_rejected(self):
            with self.assertRaises(ValueError):
                suggest_table('a', 2, ('T2',), self.rows)

        def test_duplicate_inventory_rejected(self):
            with self.assertRaises(ValueError):
                suggest_table('a', 2, ('T8',), self.rows + (Candidate('a', 'T8', 6),))

        def test_duplicate_available_rejected(self):
            with self.assertRaises(ValueError):
                suggest_table('a', 2, ('T8', 'T8'), self.rows)

        def test_bool_party_capacity_rejected(self):
            with self.assertRaises(ValueError):
                suggest_table('a', True, ('T8',), self.rows)
            with self.assertRaises(ValueError):
                suggest_table('a', 2, ('T8',), (Candidate('a', 'T8', True),))

        def test_unknown_table_rejected(self):
            with self.assertRaises(ValueError):
                suggest_table('a', 2, ('missing',), self.rows)

    unittest.main()
