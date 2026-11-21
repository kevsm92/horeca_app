"""Pure synthetic-only occupancy projection. No persistence or authenticated API."""
from dataclasses import dataclass
from enum import Enum


class Status(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    CONFLICT = "conflict"
    OUT_OF_SERVICE = "out_of_service"


@dataclass(frozen=True)
class PhysicalTable:
    venue_id: str
    table_id: str
    capacity: int
    in_service: bool = True


@dataclass(frozen=True)
class Seating:
    venue_id: str
    table_id: str
    session_id: str
    guests: int
    active: bool = True


def project(table: PhysicalTable, sessions: list[Seating]) -> tuple[Status, int]:
    """Return status and active guest count; never silently resolve conflicts."""
    if not table.venue_id or not table.table_id or table.capacity < 1:
        raise ValueError("invalid physical table")
    relevant = [s for s in sessions if s.active and s.venue_id == table.venue_id
                and s.table_id == table.table_id]
    if any(not s.session_id or s.guests < 1 for s in relevant):
        raise ValueError("invalid active seating")
    guests = sum(s.guests for s in relevant)
    if len(relevant) > 1 or guests > table.capacity:
        return Status.CONFLICT, guests
    if not table.in_service:
        return (Status.CONFLICT if relevant else Status.OUT_OF_SERVICE), guests
    return (Status.OCCUPIED if relevant else Status.AVAILABLE), guests


if __name__ == "__main__":
    import unittest

    class ProjectionTests(unittest.TestCase):
        def setUp(self):
            self.table = PhysicalTable("venue-a", "T1", 4)

        def test_empty(self):
            self.assertEqual(project(self.table, []), (Status.AVAILABLE, 0))

        def test_active_and_closed(self):
            rows = [Seating("venue-a", "T1", "s1", 2),
                    Seating("venue-a", "T1", "old", 4, False)]
            self.assertEqual(project(self.table, rows), (Status.OCCUPIED, 2))

        def test_cross_venue_and_table_isolation(self):
            rows = [Seating("venue-b", "T1", "s1", 3),
                    Seating("venue-a", "T2", "s2", 2)]
            self.assertEqual(project(self.table, rows), (Status.AVAILABLE, 0))

        def test_double_seating_is_conflict(self):
            rows = [Seating("venue-a", "T1", "s1", 1),
                    Seating("venue-a", "T1", "s2", 1)]
            self.assertEqual(project(self.table, rows), (Status.CONFLICT, 2))

        def test_over_capacity_is_conflict(self):
            self.assertEqual(project(self.table, [Seating("venue-a", "T1", "s1", 5)]),
                             (Status.CONFLICT, 5))

        def test_out_of_service(self):
            table = PhysicalTable("venue-a", "T1", 4, False)
            self.assertEqual(project(table, []), (Status.OUT_OF_SERVICE, 0))
            self.assertEqual(project(table, [Seating("venue-a", "T1", "s1", 2)]),
                             (Status.CONFLICT, 2))

        def test_invalid_inputs(self):
            with self.assertRaises(ValueError):
                project(PhysicalTable("venue-a", "T1", 0), [])
            with self.assertRaises(ValueError):
                project(self.table, [Seating("venue-a", "T1", "s1", 0)])

    unittest.main()
