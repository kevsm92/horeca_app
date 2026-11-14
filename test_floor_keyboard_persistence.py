"""Synthetic integration test: keyboard intent persisted through revision-checked SQLite CAS.

Offline only; no authentication, HTTP routes or production seating changes.
"""
import sqlite3
import unittest

from floor_keyboard_step import keyboard_move
from prototypes.sqlite_floorplan_cas import init, save


def move_with_keyboard(db, venue, plan, table_id, expected_revision, key,
                       *, table_width_mm, table_height_mm, floor_width_mm,
                       floor_height_mm, shift=False):
    """Reject stale/cross-venue moves before deriving and persisting new coordinates."""
    if any(not isinstance(s, str) or not s for s in (venue, plan, table_id)):
        raise ValueError('invalid scope')
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError('invalid revision')
    row = db.execute(
        'SELECT x,y,revision FROM positions WHERE venue=? AND plan=? AND table_id=?',
        (venue, plan, table_id),
    ).fetchone()
    if row is None or row[2] != expected_revision:
        raise ValueError('missing or stale position')
    x, y = keyboard_move(row[0], row[1], table_width_mm, table_height_mm,
                         floor_width_mm, floor_height_mm, key, shift=shift)
    if (x, y) == row[:2]:
        return expected_revision  # Boundary no-op does not create a revision.
    return save(db, venue, plan, table_id, expected_revision, x, y,
                floor_width_mm - table_width_mm + 1,
                floor_height_mm - table_height_mm + 1)


class KeyboardPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        init(self.db)
        self.db.execute("INSERT INTO positions VALUES ('venue-a','room-1','T1',100,100,2)")
        self.kw = dict(table_width_mm=400, table_height_mm=400,
                       floor_width_mm=1000, floor_height_mm=800)

    def tearDown(self):
        self.db.close()

    def move(self, revision, key, **kwargs):
        return move_with_keyboard(self.db, 'venue-a', 'room-1', 'T1', revision,
                                  key, **{**self.kw, **kwargs})

    def test_arrow_persists_and_revision_increments(self):
        self.assertEqual(self.move(2, 'ArrowRight'), 3)
        self.assertEqual(self.db.execute('SELECT x,y,revision FROM positions').fetchone(),
                         (150, 100, 3))

    def test_shift_move_and_clamp_to_footprint(self):
        self.assertEqual(self.move(2, 'ArrowDown', shift=True), 3)
        self.assertEqual(self.db.execute('SELECT x,y FROM positions').fetchone(), (100, 350))

    def test_stale_write_cannot_overwrite(self):
        self.move(2, 'ArrowRight')
        with self.assertRaises(ValueError):
            self.move(2, 'ArrowLeft')
        self.assertEqual(self.db.execute('SELECT x,y,revision FROM positions').fetchone(),
                         (150, 100, 3))

    def test_wrong_venue_rejected(self):
        with self.assertRaises(ValueError):
            move_with_keyboard(self.db, 'venue-b', 'room-1', 'T1', 2,
                               'ArrowRight', **self.kw)

    def test_boundary_noop_does_not_bump_revision(self):
        self.db.execute("UPDATE positions SET x=0 WHERE table_id='T1'")
        self.assertEqual(self.move(2, 'ArrowLeft'), 2)
        self.assertEqual(self.db.execute('SELECT revision FROM positions').fetchone(), (2,))

    def test_rejects_invalid_geometry_and_bool_revision(self):
        with self.assertRaises(ValueError):
            self.move(True, 'ArrowRight')
        with self.assertRaises(ValueError):
            self.move(2, 'ArrowRight', table_width_mm=1100)


if __name__ == '__main__':
    unittest.main()
