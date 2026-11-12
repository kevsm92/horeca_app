"""Offline, synthetic-only Tables occupancy projection prototype.

Run: python -m unittest discover -s prototypes -p 'test_tables_projection.py'
Not wired to authentication, a database, or the HORECA UI.
"""
from dataclasses import dataclass
import unittest


class IntegrityError(ValueError):
    """Fail closed: do not display a misleading available status."""


@dataclass(frozen=True)
class PhysicalTable:
    id: str
    venue_id: str
    label: str
    capacity: int
    enabled: bool


@dataclass(frozen=True)
class SeatingSession:
    id: str
    venue_id: str
    table_id: str
    guests: int
    active: bool


def project_occupancy(venue_id, tables, sessions):
    """Return minimal, deterministic table rows; reject corrupt inputs."""
    if not isinstance(venue_id, str) or not venue_id:
        raise IntegrityError("missing venue context")
    by_id = {}
    for table in tables:
        if (table.venue_id != venue_id or not table.id or
                table.id in by_id or type(table.capacity) is not int or
                table.capacity < 1 or type(table.enabled) is not bool):
            raise IntegrityError("invalid physical table")
        by_id[table.id] = table
    active = {}
    session_ids = set()
    for session in sessions:
        if session.venue_id != venue_id or not session.id or session.id in session_ids:
            raise IntegrityError("invalid seating session")
        session_ids.add(session.id)
        if not session.active:
            continue
        table = by_id.get(session.table_id)
        if (table is None or session.table_id in active or
                type(session.guests) is not int or
                not 1 <= session.guests <= table.capacity):
            raise IntegrityError("invalid active seating")
        active[session.table_id] = session.guests
    return [
        {"id": table.id, "label": table.label, "capacity": table.capacity,
         "occupied_guests": active.get(table.id, 0),
         "status": ("occupied" if table.id in active else
                    "available" if table.enabled else "unavailable")}
        for table in sorted(by_id.values(), key=lambda item: item.id)
    ]


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.table = PhysicalTable("t1", "v1", "Window", 4, True)
        self.session = SeatingSession("s1", "v1", "t1", 2, True)

    def test_available(self):
        self.assertEqual(project_occupancy("v1", [self.table], [])[0]["status"], "available")

    def test_occupied(self):
        row = project_occupancy("v1", [self.table], [self.session])[0]
        self.assertEqual((row["status"], row["occupied_guests"]), ("occupied", 2))

    def test_disabled_empty(self):
        table = PhysicalTable("t1", "v1", "Window", 4, False)
        self.assertEqual(project_occupancy("v1", [table], [])[0]["status"], "unavailable")

    def test_disabled_occupied_remains_occupied(self):
        table = PhysicalTable("t1", "v1", "Window", 4, False)
        self.assertEqual(project_occupancy("v1", [table], [self.session])[0]["status"], "occupied")

    def test_inactive_ignored(self):
        session = SeatingSession("s1", "v1", "t1", 2, False)
        self.assertEqual(project_occupancy("v1", [self.table], [session])[0]["occupied_guests"], 0)

    def test_sorting(self):
        other = PhysicalTable("a", "v1", "Bar", 1, True)
        self.assertEqual([r["id"] for r in project_occupancy("v1", [self.table, other], [])], ["a", "t1"])

    def test_duplicate_tables(self):
        with self.assertRaises(IntegrityError):
            project_occupancy("v1", [self.table, self.table], [])

    def test_double_seating(self):
        with self.assertRaises(IntegrityError):
            project_occupancy("v1", [self.table, self.session,], [self.session, SeatingSession("s2", "v1", "t1", 1, True)])

    def test_orphan(self):
        with self.assertRaises(IntegrityError):
            project_occupancy("v1", [], [self.session])

    def test_cross_venue_table(self):
        with self.assertRaises(IntegrityError):
            project_occupancy("v2", [self.table], [])

    def test_cross_venue_session(self):
        with self.assertRaises(IntegrityError):
            project_occupancy("v1", [self.table], [SeatingSession("s1", "v2", "t1", 2, True)])

    def test_over_capacity(self):
        with self.assertRaises(IntegrityError):
            project_occupancy("v1", [self.table], [SeatingSession("s1", "v1", "t1", 5, True)])

    def test_zero_guests(self):
        with self.assertRaises(IntegrityError):
            project_occupancy("v1", [self.table], [SeatingSession("s1", "v1", "t1", 0, True)])

    def test_boolean_capacity_rejected(self):
        with self.assertRaises(IntegrityError):
            project_occupancy("v1", [PhysicalTable("t1", "v1", "Window", True, True)], [])

    def test_duplicate_session_ids(self):
        with self.assertRaises(IntegrityError):
            project_occupancy("v1", [self.table], [self.session, self.session])

    def test_no_venue(self):
        with self.assertRaises(IntegrityError):
            project_occupancy("", [self.table], [])


if __name__ == "__main__":
    unittest.main()
