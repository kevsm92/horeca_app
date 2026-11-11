"""Offline venue-scoped table seating prototype; NOT concurrency-safe or persistent."""
from dataclasses import dataclass
import unittest
from threading import RLock
from functools import wraps

def synchronized(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return guarded

@dataclass(frozen=True)
class PhysicalTable:
    venue_id: str
    table_id: str
    capacity: int
    active: bool = True

    def __post_init__(self):
        if not self.venue_id or not self.table_id or not isinstance(self.capacity, int) or isinstance(self.capacity, bool) or self.capacity < 1:
            raise ValueError("invalid physical table")

@dataclass(frozen=True)
class SeatingSession:
    venue_id: str
    session_id: str
    table_id: str
    guests: int
    closed: bool = False

class SeatingRegistry:
    def __init__(self):
        self._lock = RLock()
        self.tables = {}
        self.sessions = {}

    @synchronized
    def add_table(self, table):
        key = (table.venue_id, table.table_id)
        if key in self.tables:
            raise ValueError("duplicate table")
        self.tables[key] = table

    @synchronized
    def seat(self, venue_id, table_id, session_id, guests):
        table = self.tables.get((venue_id, table_id))
        if not table or not table.active:
            raise ValueError("unknown or inactive venue table")
        if not session_id or (venue_id, session_id) in self.sessions:
            raise ValueError("duplicate session")
        if not isinstance(guests, int) or isinstance(guests, bool) or not 1 <= guests <= table.capacity:
            raise ValueError("invalid guest count")
        if any(s.venue_id == venue_id and s.table_id == table_id and not s.closed for s in self.sessions.values()):
            raise ValueError("double seating")
        session = SeatingSession(venue_id, session_id, table_id, guests)
        self.sessions[(venue_id, session_id)] = session
        return session

    @synchronized
    def close(self, venue_id, session_id):
        key = (venue_id, session_id)
        s = self.sessions.get(key)
        if not s or s.closed:
            raise ValueError("unknown or closed session")
        self.sessions[key] = SeatingSession(s.venue_id, s.session_id, s.table_id, s.guests, True)

class Tests(unittest.TestCase):
    def setUp(self):
        self.r = SeatingRegistry()
        self.r.add_table(PhysicalTable("a", "T1", 4))
        self.r.add_table(PhysicalTable("b", "T1", 2))

    def test_concurrent_seating_one_winner(self):
        from concurrent.futures import ThreadPoolExecutor
        def attempt(i):
            try:
                self.r.seat("a", "T1", f"concurrent-{i}", 2)
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=12) as executor:
            outcomes = list(executor.map(attempt, range(40)))
        self.assertEqual(sum(outcomes), 1)

    def test_double_seating_and_close(self):
        self.r.seat("a", "T1", "s1", 4)
        with self.assertRaises(ValueError):
            self.r.seat("a", "T1", "s2", 1)
        self.r.close("a", "s1")
        self.r.seat("a", "T1", "s2", 1)

    def test_venue_isolation(self):
        with self.assertRaises(ValueError):
            self.r.seat("c", "T1", "s1", 1)
        self.r.seat("a", "T1", "s1", 2)
        self.r.seat("b", "T1", "s1", 2)

    def test_capacity(self):
        for n in (0, -1, 5, True, 1.5):
            with self.subTest(n=n), self.assertRaises(ValueError):
                self.r.seat("a", "T1", "s1", n)

    def test_duplicate_ids(self):
        with self.assertRaises(ValueError):
            self.r.add_table(PhysicalTable("a", "T1", 6))
        self.r.seat("a", "T1", "s1", 1)
        self.r.close("a", "s1")
        with self.assertRaises(ValueError):
            self.r.seat("a", "T1", "s1", 1)

    def test_inactive_and_invalid_capacity(self):
        with self.assertRaises(ValueError):
            PhysicalTable("a", "bad", 0)
        self.r.add_table(PhysicalTable("a", "T2", 2, False))
        with self.assertRaises(ValueError):
            self.r.seat("a", "T2", "s1", 1)

if __name__ == "__main__":
    unittest.main()
