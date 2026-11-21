import unittest
from datetime import datetime, timezone, timedelta
from waitlist import WaitEntry, candidates

T = datetime(2026, 11, 16, 18, tzinfo=timezone.utc)
def entry(id, venue="v1", guests=2, offset=0, status="waiting"):
    return WaitEntry(id, venue, guests, T + timedelta(minutes=offset), T, T + timedelta(hours=2), status)

class WaitlistTests(unittest.TestCase):
    def test_fifo_and_tie_break(self):
        self.assertEqual(candidates([entry("z"),entry("a"),entry("b",offset=-2)],venue_id="v1",available_at=T,capacity=2),["b","a","z"])
    def test_tenant_capacity_and_status(self):
        self.assertEqual(candidates([entry("a","v2"),entry("b",guests=5),entry("c",status="cancelled"),entry("d")],venue_id="v1",available_at=T,capacity=4),["d"])
    def test_time_window(self):
        self.assertEqual(candidates([entry("a")],venue_id="v1",available_at=T+timedelta(hours=3),capacity=2),[])
    def test_reject_naive_time(self):
        with self.assertRaises(ValueError):
            candidates([entry("a")],venue_id="v1",available_at=datetime(2026,11,16),capacity=2)
    def test_no_mutation(self):
        items=[entry("a")]
        candidates(items,venue_id="v1",available_at=T,capacity=2)
        self.assertEqual(items[0].status,"waiting")

if __name__ == "__main__":
    unittest.main()
