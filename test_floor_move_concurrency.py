"""Synthetic multi-connection regression for SQLite floor-plan move CAS + audit.

Run: python -m unittest -v test_floor_move_concurrency
"""
import os
import sqlite3
import tempfile
import threading
import unittest

from floor_position_audit import install_audit
from prototypes.sqlite_floorplan_cas import init, save


class ConcurrentMoveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'floor.db')
        with sqlite3.connect(self.path) as db:
            init(db)
            install_audit(db)
            db.execute("INSERT INTO positions VALUES ('venue-a','room','T1',10,20,0)")
            db.execute("INSERT INTO positions VALUES ('venue-b','room','T1',50,60,0)")

    def tearDown(self):
        self.tmp.cleanup()

    def test_simultaneous_same_revision_one_winner_one_audit(self):
        barrier = threading.Barrier(2)
        results = []
        lock = threading.Lock()

        def move(x):
            with sqlite3.connect(self.path, timeout=5) as db:
                barrier.wait(timeout=5)
                try:
                    result = ('ok', x, save(db, 'venue-a','room','T1',0,x,40,100,100))
                except ValueError:
                    result = ('stale', x)
                with lock:
                    results.append(result)

        threads = [threading.Thread(target=move, args=(x,)) for x in (30,70)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(sorted(r[0] for r in results), ['ok','stale'])
        with sqlite3.connect(self.path) as db:
            x,y,revision = db.execute("SELECT x,y,revision FROM positions WHERE venue='venue-a'").fetchone()
            self.assertIn(x,(30,70))
            self.assertEqual((y,revision),(40,1))
            self.assertEqual(db.execute("SELECT old_x,new_x,old_revision,new_revision FROM position_move_audit WHERE venue='venue-a'").fetchall(), [(10,x,0,1)])
            self.assertEqual(db.execute("SELECT x,y,revision FROM positions WHERE venue='venue-b'").fetchone(), (50,60,0))

    def test_stale_retry_creates_no_second_event(self):
        with sqlite3.connect(self.path) as db:
            save(db,'venue-a','room','T1',0,30,40,100,100)
        with sqlite3.connect(self.path) as db:
            with self.assertRaises(ValueError):
                save(db,'venue-a','room','T1',0,70,40,100,100)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM position_move_audit").fetchone()[0],1)


if __name__ == '__main__':
    unittest.main()
