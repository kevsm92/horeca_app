"""Focused synthetic tests for offline manager hourly order KPI series."""
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from manager_order_hourly_series import accepted_order_hourly_series

class HourlyOrderSeriesTests(unittest.TestCase):
    def setUp(self):
        self.manager = SimpleNamespace(authenticated=True, role="manager", venue_id="synthetic-a")
        self.start = datetime(2026, 11, 28, 8, tzinfo=timezone.utc)
        self.end = self.start + timedelta(hours=2)

    def series(self, orders):
        return accepted_order_hourly_series(principal=self.manager, orders=orders, start=self.start, end=self.end)

    def test_hour_boundaries_and_money(self):
        rows = [
            dict(venue_id="synthetic-a", id="a", status="accepted", total_cents=1999, accepted_at=self.start),
            dict(venue_id="synthetic-a", id="b", status="accepted", total_cents=250, accepted_at=self.start + timedelta(hours=1)),
            dict(venue_id="synthetic-a", id="c", status="accepted", total_cents=900, accepted_at=self.end),
            dict(venue_id="synthetic-b", id="d", status="accepted", total_cents=900, accepted_at=self.start)]
        result = self.series(rows)
        self.assertEqual([x["accepted_value_cents"] for x in result["hours"]], [1999, 250])
        self.assertEqual([x["accepted_orders"] for x in result["hours"]], [1, 1])
        self.assertIsNone(result["captured_revenue"])
        self.assertFalse(result["is_live"])

    def test_unknown_not_zero(self):
        self.assertIsNone(self.series(None)["hours"][0]["accepted_orders"])
        self.assertEqual(self.series([])["hours"][0]["accepted_orders"], 0)

    def test_manager_auth(self):
        for role, authenticated in [("staff", True), ("manager", False)]:
            with self.assertRaises(PermissionError):
                accepted_order_hourly_series(principal=SimpleNamespace(role=role, authenticated=authenticated, venue_id="synthetic-a"), orders=[], start=self.start, end=self.end)

    def test_invalid_records(self):
        row = dict(venue_id="synthetic-a", id="a", status="accepted", total_cents=100, accepted_at=self.start)
        for records in ([row, row], [{**row, "total_cents": True}], [{**row, "accepted_at": self.start.replace(tzinfo=None)}]):
            with self.assertRaises(ValueError):
                self.series(records)

    def test_max_range(self):
        with self.assertRaises(ValueError):
            accepted_order_hourly_series(principal=self.manager, orders=[], start=self.start, end=self.start + timedelta(hours=169))

if __name__ == "__main__":
    unittest.main()
