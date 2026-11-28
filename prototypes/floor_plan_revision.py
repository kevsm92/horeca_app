"""Offline floor-plan optimistic movement reference, not an authenticated API."""
from dataclasses import dataclass
from math import isfinite
import unittest

class FloorPlanConflict(ValueError):
    """Invalid, stale or cross-venue movement."""

@dataclass(frozen=True)
class TablePosition:
    venue_id: str
    table_id: str
    x: float
    y: float
    revision: int

def move_table(current: TablePosition, *, venue_id: str, table_id: str,
               expected_revision: int, x: float, y: float) -> TablePosition:
    """Normalized [0,1] coordinates; caller must authorize and persist via atomic CAS."""
    if not venue_id or not table_id or (current.venue_id, current.table_id) != (venue_id, table_id):
        raise FloorPlanConflict("table not found in venue")
    if type(expected_revision) is not int or expected_revision != current.revision:
        raise FloorPlanConflict("stale revision")
    if any(type(v) not in (int, float) or not isfinite(v) or not 0 <= v <= 1 for v in (x, y)):
        raise FloorPlanConflict("invalid coordinates")
    return TablePosition(venue_id, table_id, float(x), float(y), current.revision + 1)

class MovementTests(unittest.TestCase):
    def setUp(self):
        self.current = TablePosition("venue-a", "table-1", .2, .3, 4)
        self.args = dict(venue_id="venue-a", table_id="table-1", expected_revision=4, x=.5, y=.6)

    def test_move_and_immutable_old_revision(self):
        result = move_table(self.current, **self.args)
        self.assertEqual((result.x, result.y, result.revision), (.5, .6, 5))
        self.assertEqual(self.current.revision, 4)

    def test_stale_revision(self):
        with self.assertRaises(FloorPlanConflict):
            move_table(self.current, **{**self.args, "expected_revision": 3})

    def test_venue_isolation(self):
        with self.assertRaises(FloorPlanConflict):
            move_table(self.current, **{**self.args, "venue_id": "venue-b"})

    def test_table_identity(self):
        with self.assertRaises(FloorPlanConflict):
            move_table(self.current, **{**self.args, "table_id": "table-2"})

    def test_invalid_coordinates(self):
        for v in (-.1, 1.1, float("nan"), float("inf"), True, "0.5"):
            with self.subTest(v=v), self.assertRaises(FloorPlanConflict):
                move_table(self.current, **{**self.args, "x": v})

    def test_boolean_revision(self):
        with self.assertRaises(FloorPlanConflict):
            move_table(self.current, **{**self.args, "expected_revision": True})

if __name__ == "__main__":
    unittest.main()
