"""Synthetic, offline accessibility regression for saved table geometry."""
import unittest
from table_resize_announcement import saved_resize_announcement as announce


class ResizeAnnouncementTests(unittest.TestCase):
    def test_committed_geometry_and_seats_are_explicit(self):
        self.assertEqual(announce('A1', '120.5', '80.0', 4, 3),
                         'Table A1: saved width 120.5 cm, depth 80.0 cm, 4 seats. Revision 3.')

    def test_rejects_uncommitted_or_invalid_revision(self):
        for value in (0, -1, True, 1.0, '1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                announce('A1', '80.0', '80.0', 4, value)

    def test_rejects_invalid_geometry(self):
        for value in ('NaN', 'Infinity', '29.5', '500.5', '80.1', 'bad', '', 80):
            with self.subTest(value=value), self.assertRaises(ValueError):
                announce('A1', value, '80.0', 4, 1)

    def test_rejects_unsafe_label_and_seat_counts(self):
        for label in ('', 'x'*41, 'A\nB', 'A\x00B', None):
            with self.subTest(label=label), self.assertRaises(ValueError):
                announce(label, '80.0', '80.0', 4, 1)
        for seats in (0, 101, True, 4.0, '4'):
            with self.subTest(seats=seats), self.assertRaises(ValueError):
                announce('A1', '80.0', '80.0', seats, 1)


if __name__ == '__main__':
    unittest.main()
