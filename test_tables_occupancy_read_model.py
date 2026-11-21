"""Synthetic regression tests for the standalone Tables occupancy projection."""
import unittest
from prototypes.tables_occupancy_read_model import project_occupancy


class OccupancyTests(unittest.TestCase):
    def test_available_and_occupied_are_distinct(self):
        rows = project_occupancy([("T1", 2), ("T2", 4)], [("T2", 3)])
        self.assertEqual([(r.table_id, r.status, r.guests) for r in rows],
                         [("T1", "available", 0), ("T2", "occupied", 3)])

    def test_capacity_boundary(self):
        self.assertEqual(project_occupancy([("T1", 2)], [("T1", 2)])[0].guests, 2)

    def test_duplicate_active_session_fails_closed(self):
        with self.assertRaises(ValueError):
            project_occupancy([("T1", 2)], [("T1", 1), ("T1", 1)])

    def test_unknown_table_fails_closed(self):
        with self.assertRaises(ValueError):
            project_occupancy([("T1", 2)], [("OTHER", 1)])

    def test_capacity_overflow_fails_closed(self):
        with self.assertRaises(ValueError):
            project_occupancy([("T1", 2)], [("T1", 3)])

    def test_invalid_inventory_fails_closed(self):
        for inventory in [[("T1", 2), ("T1", 2)], [("T1", 0)], [("T1", True)]]:
            with self.subTest(inventory=inventory), self.assertRaises(ValueError):
                project_occupancy(inventory, [])

    def test_invalid_guest_counts_fails_closed(self):
        for guests in [0, -1, 1.5, True]:
            with self.subTest(guests=guests), self.assertRaises(ValueError):
                project_occupancy([("T1", 2)], [("T1", guests)])


if __name__ == "__main__":
    unittest.main()
