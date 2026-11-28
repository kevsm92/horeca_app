import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from manager_reservation_kpis import reservation_kpis

NOW = datetime(2026, 11, 28, 4, tzinfo=timezone.utc)
P = SimpleNamespace(authenticated=True, role="manager", venue_id="fictional-a")

class Tests(unittest.TestCase):
    def test_isolation_and_counts(self):
        rows = [dict(id="a", venue_id="fictional-a", status="confirmed", starts_at=NOW),
                dict(id="b", venue_id="fictional-a", status="seated", starts_at=NOW),
                dict(id="c", venue_id="fictional-b", status="confirmed", starts_at=NOW)]
        result = reservation_kpis(principal=P, reservations=rows, as_of=NOW)
        self.assertEqual(result["upcoming_reservations"]["value"], 1)
        self.assertEqual(result["seated_reservations"]["value"], 1)
        self.assertFalse(result["is_live"])

    def test_unavailable_distinct_from_zero(self):
        self.assertIsNone(reservation_kpis(principal=P, reservations=None, as_of=NOW)["upcoming_reservations"]["value"])
        self.assertEqual(reservation_kpis(principal=P, reservations=[], as_of=NOW)["upcoming_reservations"]["value"], 0)

    def test_auth(self):
        for p in (SimpleNamespace(authenticated=False, role="manager", venue_id="fictional-a"),
                  SimpleNamespace(authenticated=True, role="staff", venue_id="fictional-a"),
                  SimpleNamespace(authenticated=True, role="manager", venue_id="")):
            with self.assertRaises(PermissionError):
                reservation_kpis(principal=p, reservations=[], as_of=NOW)

    def test_invalid_records(self):
        row = dict(id="a", venue_id="fictional-a", status="confirmed", starts_at=NOW)
        for bad in (dict(row, status="invalid"), dict(row, starts_at=NOW.replace(tzinfo=None)),
                    dict(row, status="seated", starts_at=NOW + timedelta(seconds=1))):
            with self.assertRaises(ValueError):
                reservation_kpis(principal=P, reservations=[bad], as_of=NOW)
        with self.assertRaises(ValueError):
            reservation_kpis(principal=P, reservations=[row, row], as_of=NOW)

if __name__ == "__main__":
    unittest.main()
