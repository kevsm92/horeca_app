import unittest
from datetime import datetime, timedelta, timezone
from roster_revision import Shift, RosterConflict, propose_revision

BASE = datetime(2026, 11, 30, 9, tzinfo=timezone.utc)

def shift(start, end, staff='fictional-1'):
    return Shift(staff, BASE + timedelta(hours=start), BASE + timedelta(hours=end), 'kitchen')

class RosterRevisionTests(unittest.TestCase):
    def propose(self, shifts=(), current=0, expected=0, venue='demo-a'):
        return propose_revision(current_revision=current, expected_revision=expected,
            current_venue='demo-a', requested_venue=venue, shifts=shifts)

    def test_adjacent(self):
        self.assertEqual(self.propose((shift(0, 4), shift(4, 8)), 3, 3), 4)
    def test_overlap(self):
        with self.assertRaises(RosterConflict):
            self.propose((shift(0, 4), shift(3, 5)))
    def test_different_staff(self):
        self.assertEqual(self.propose((shift(0, 4), shift(0, 4, 'fictional-2'))), 1)
    def test_stale(self):
        with self.assertRaises(RosterConflict):
            self.propose(current=2, expected=1)
    def test_cross_venue(self):
        with self.assertRaises(PermissionError):
            self.propose(venue='demo-b')
    def test_naive(self):
        with self.assertRaises(ValueError):
            self.propose((Shift('fictional-1', BASE.replace(tzinfo=None), BASE, 'bar'),))
    def test_reverse(self):
        with self.assertRaises(ValueError):
            self.propose((shift(4, 2),))
    def test_cross_midnight(self):
        self.assertEqual(self.propose((shift(13, 19),)), 1)

if __name__ == '__main__':
    unittest.main()
