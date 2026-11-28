import unittest
from datetime import datetime, timedelta, timezone
from roster_conflicts import roster_conflicts


class RosterConflictTests(unittest.TestCase):
    def setUp(self):
        self.t = datetime(2026, 11, 27, 8, tzinfo=timezone.utc)

    def shift(self, ident, start=0, end=2, staff='fictional-1', venue='A'):
        return dict(id=ident, staff_id=staff, venue_id=venue,
                    start_utc=self.t + timedelta(hours=start),
                    end_utc=self.t + timedelta(hours=end))

    def test_overlap_and_touching_boundary(self):
        result = roster_conflicts([self.shift('a'), self.shift('b', 1, 3),
                                   self.shift('c', 3, 5)], 'A')
        self.assertEqual(result['conflicts'], [dict(staff_id='fictional-1',
                            shift_ids=['a', 'b'], reason='overlap')])

    def test_cross_venue_and_different_staff(self):
        rows = [self.shift('a'), self.shift('b', 1, 3, venue='B'),
                self.shift('c', 1, 3, staff='fictional-2')]
        self.assertEqual(roster_conflicts(rows, 'A')['conflicts'], [])

    def test_invalid_interval_and_duplicate_id(self):
        with self.assertRaises(ValueError):
            roster_conflicts([self.shift('a', 2, 1)], 'A')
        with self.assertRaises(ValueError):
            roster_conflicts([self.shift('a'), self.shift('a', 3, 4)], 'A')

    def test_naive_time_rejected(self):
        bad = self.shift('a')
        bad['start_utc'] = bad['start_utc'].replace(tzinfo=None)
        with self.assertRaises(ValueError):
            roster_conflicts([bad], 'A')


if __name__ == '__main__':
    unittest.main()
