"""Real-file SQLite concurrency regression tests; synthetic venues only."""
import os
import sqlite3
import tempfile
import threading
import unittest

from tables_foundation import connect, seat


class ConcurrentSeatingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp.name, "tables.sqlite3")
        db = connect(self.path)
        db.executemany("INSERT INTO physical_tables VALUES (?,?,?)",
                       [("v1", "t1", 4), ("v1", "t2", 4), ("v2", "t1", 2)])
        db.close()

    def tearDown(self):
        self.temp.cleanup()

    def compete(self, assignments):
        barrier = threading.Barrier(len(assignments))
        outcomes = []
        lock = threading.Lock()

        def worker(session_id, venue_id, table_id):
            db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
            db.execute("PRAGMA foreign_keys=ON")
            try:
                barrier.wait(timeout=5)
                seat(db, session_id, venue_id, table_id, 1)
                result = "seated"
            except sqlite3.IntegrityError:
                result = "conflict"
            finally:
                db.close()
            with lock:
                outcomes.append(result)

        threads = [threading.Thread(target=worker, args=assignment)
                   for assignment in assignments]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
            self.assertFalse(thread.is_alive(), "concurrent seat operation hung")
        return outcomes

    def test_competing_sessions_exactly_one_wins(self):
        outcomes = self.compete([("s1", "v1", "t1"), ("s2", "v1", "t1")])
        self.assertCountEqual(outcomes, ["seated", "conflict"])
        db = connect(self.path)
        try:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM seating_sessions WHERE status='active'").fetchone()[0], 1)
        finally:
            db.close()

    def test_different_tables_and_venues_can_seat_concurrently(self):
        outcomes = self.compete([("s1", "v1", "t1"), ("s2", "v1", "t2"),
                                 ("s3", "v2", "t1")])
        self.assertEqual(outcomes.count("seated"), 3)


if __name__ == "__main__":
    unittest.main()
