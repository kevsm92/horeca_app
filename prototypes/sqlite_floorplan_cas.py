"""Offline SQLite CAS prototype for durable floor-plan positions; synthetic only."""
import sqlite3
import unittest

def init(db):
    db.execute('CREATE TABLE positions (venue TEXT NOT NULL, plan TEXT NOT NULL, table_id TEXT NOT NULL, x INTEGER NOT NULL, y INTEGER NOT NULL, revision INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (venue, plan, table_id))')

def save(db, venue, plan, table_id, expected_revision, x, y, width, height):
    if any(type(v) is not int for v in (expected_revision, x, y, width, height)):
        raise ValueError('integer values required')
    if expected_revision < 0 or width <= 0 or height <= 0 or not (0 <= x < width and 0 <= y < height):
        raise ValueError('invalid bounds')
    with db:
        cursor = db.execute('UPDATE positions SET x=?, y=?, revision=revision+1 WHERE venue=? AND plan=? AND table_id=? AND revision=?', (x, y, venue, plan, table_id, expected_revision))
        if cursor.rowcount != 1:
            raise ValueError('not found, wrong venue or stale revision')
    return expected_revision + 1

class Tests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        init(self.db)
        self.db.execute("INSERT INTO positions VALUES ('v1','p1','t1',10,20,0)")
        self.args = ('v1', 'p1', 't1', 0, 30, 40, 500, 300)

    def tearDown(self):
        self.db.close()

    def test_persist_and_increment(self):
        self.assertEqual(save(self.db, *self.args), 1)
        self.assertEqual(self.db.execute('SELECT x,y,revision FROM positions').fetchone(), (30,40,1))

    def test_stale_rejected_without_overwrite(self):
        save(self.db, *self.args)
        with self.assertRaises(ValueError):
            save(self.db, *self.args)
        self.assertEqual(self.db.execute('SELECT x,y,revision FROM positions').fetchone(), (30,40,1))

    def test_wrong_scope_rejected(self):
        for index in (0,1,2):
            args = list(self.args)
            args[index] = 'other'
            with self.assertRaises(ValueError):
                save(self.db, *args)

    def test_invalid_coordinates_rejected(self):
        for index, value in ((4,-1),(5,300),(4,True),(6,0),(7,-1)):
            args = list(self.args)
            args[index] = value
            with self.assertRaises(ValueError):
                save(self.db, *args)

if __name__ == '__main__':
    unittest.main(verbosity=2)
