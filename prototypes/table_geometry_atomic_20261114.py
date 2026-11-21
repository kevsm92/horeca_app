"""Synthetic offline SQLite reference for revision-checked visual geometry updates.

Geometry is deliberately independent of physical seat inventory and occupancy.
Caller must authorize venue/table before invoking this primitive.
"""
import sqlite3
import unittest


def install(db):
    db.execute('''CREATE TABLE tables (
        venue_id TEXT NOT NULL, table_id TEXT NOT NULL,
        width_cm INTEGER NOT NULL CHECK(width_cm BETWEEN 40 AND 400),
        depth_cm INTEGER NOT NULL CHECK(depth_cm BETWEEN 40 AND 400),
        x INTEGER NOT NULL, y INTEGER NOT NULL,
        physical_seats INTEGER NOT NULL CHECK(physical_seats BETWEEN 1 AND 100),
        configured_seats INTEGER NOT NULL CHECK(configured_seats BETWEEN 1 AND physical_seats),
        seated_guests INTEGER NOT NULL CHECK(seated_guests BETWEEN 0 AND configured_seats),
        revision INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(venue_id,table_id))''')


def resize_geometry(db, venue_id, table_id, expected_revision, width_cm, depth_cm):
    if not all(type(v) is str and v for v in (venue_id, table_id)):
        raise ValueError('venue and table required')
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError('invalid revision')
    if any(type(v) is not int or not 40 <= v <= 400 for v in (width_cm, depth_cm)):
        raise ValueError('invalid visual dimensions')
    db.execute('BEGIN IMMEDIATE')
    try:
        cur = db.execute('''UPDATE tables SET width_cm=?,depth_cm=?,revision=revision+1
            WHERE venue_id=? AND table_id=? AND revision=?''',
            (width_cm, depth_cm, venue_id, table_id, expected_revision))
        if cur.rowcount != 1:
            raise ValueError('stale revision or table not in venue')
        db.commit()
    except BaseException:
        db.rollback()
        raise
    return expected_revision + 1


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        install(self.db)
        self.db.execute("INSERT INTO tables VALUES ('a','t',120,80,15,20,6,4,3,7)")
        self.db.execute("INSERT INTO tables VALUES ('b','t',120,80,30,40,4,4,0,7)")

    def tearDown(self):
        self.db.close()

    def state(self, venue='a'):
        return self.db.execute('SELECT * FROM tables WHERE venue_id=?', (venue,)).fetchone()

    def test_geometry_only_changes_and_revision_advances(self):
        self.assertEqual(resize_geometry(self.db,'a','t',7,150,90),8)
        self.assertEqual(self.state(), ('a','t',150,90,15,20,6,4,3,8))

    def test_stale_revision_has_no_effect(self):
        resize_geometry(self.db,'a','t',7,150,90)
        with self.assertRaises(ValueError):
            resize_geometry(self.db,'a','t',7,200,100)
        self.assertEqual(self.state()[2:4],(150,90))

    def test_cross_venue_scope(self):
        with self.assertRaises(ValueError):
            resize_geometry(self.db,'c','t',7,200,100)
        self.assertEqual(self.state('b'),('b','t',120,80,30,40,4,4,0,7))

    def test_invalid_inputs_are_noop(self):
        for w,d in ((True,80),(120.5,80),(0,80),(401,80),(120,'80'),(120,None)):
            with self.subTest(w=w,d=d), self.assertRaises(ValueError):
                resize_geometry(self.db,'a','t',7,w,d)
        self.assertEqual(self.state(),('a','t',120,80,15,20,6,4,3,7))

    def test_revision_type_rejected(self):
        for revision in (True,-1,'7'):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                resize_geometry(self.db,'a','t',revision,150,90)

    def test_rejects_blank_scope(self):
        with self.assertRaises(ValueError):
            resize_geometry(self.db,'','t',7,150,90)


if __name__ == '__main__':
    unittest.main()
