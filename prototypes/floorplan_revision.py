"""Offline floor-plan coordinate revision prototype. No API or durable storage."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Position:
    x: int
    y: int

class FloorPlan:
    def __init__(self, venue_id, positions, width=1000, height=800):
        if not venue_id or width <= 0 or height <= 0:
            raise ValueError("invalid floor plan")
        self.venue_id, self.width, self.height = venue_id, width, height
        self.positions = dict(positions)
        self.revision = 0
        if not all(self.valid(p) for p in self.positions.values()):
            raise ValueError("invalid initial position")

    def valid(self, p):
        return (isinstance(p, Position) and type(p.x) is int and type(p.y) is int
                and 0 <= p.x <= self.width and 0 <= p.y <= self.height)

    def move(self, venue_id, table_id, position, expected_revision):
        if venue_id != self.venue_id or table_id not in self.positions:
            raise ValueError("table does not belong to venue")
        if type(expected_revision) is not int or expected_revision != self.revision:
            raise ValueError("stale floor-plan revision")
        if not self.valid(position):
            raise ValueError("invalid position")
        if self.positions[table_id] != position:
            self.positions[table_id] = position
            self.revision += 1
        return self.revision

    def keyboard_move(self, venue_id, table_id, dx, dy, expected_revision):
        if type(dx) is not int or type(dy) is not int or abs(dx) + abs(dy) != 10:
            raise ValueError("expected one cardinal 10px step")
        if venue_id != self.venue_id or table_id not in self.positions:
            raise ValueError("table does not belong to venue")
        p = self.positions[table_id]
        return self.move(venue_id, table_id, Position(p.x + dx, p.y + dy), expected_revision)


if __name__ == "__main__":
    import unittest

    class TestFloorPlan(unittest.TestCase):
        def setUp(self):
            self.plan = FloorPlan("fictional-venue", {"T1": Position(100, 100)})

        def test_drag_and_revision(self):
            self.assertEqual(self.plan.move("fictional-venue", "T1", Position(120, 130), 0), 1)
            self.assertEqual(self.plan.positions["T1"], Position(120, 130))

        def test_stale_write_preserves_position(self):
            self.plan.move("fictional-venue", "T1", Position(120, 130), 0)
            with self.assertRaises(ValueError):
                self.plan.move("fictional-venue", "T1", Position(200, 200), 0)
            self.assertEqual(self.plan.positions["T1"], Position(120, 130))

        def test_tenant_and_table_scope(self):
            for venue, table in [("other", "T1"), ("fictional-venue", "T2")]:
                with self.assertRaises(ValueError):
                    self.plan.move(venue, table, Position(200, 200), 0)

        def test_invalid_coordinates(self):
            for p in [Position(-1, 0), Position(1001, 0), Position(True, 0)]:
                with self.assertRaises(ValueError):
                    self.plan.move("fictional-venue", "T1", p, 0)

        def test_keyboard_step(self):
            self.assertEqual(self.plan.keyboard_move("fictional-venue", "T1", 10, 0, 0), 1)
            with self.assertRaises(ValueError):
                self.plan.keyboard_move("fictional-venue", "T1", 9, 0, 1)

        def test_noop_revision(self):
            self.assertEqual(self.plan.move("fictional-venue", "T1", Position(100, 100), 0), 0)

    unittest.main(verbosity=2)
