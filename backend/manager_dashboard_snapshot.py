"""Offline manager dashboard composition; never claims live or captured revenue.

Inputs must be independently authorized, trusted domain snapshots for the same
server-derived venue and instant. Missing sources remain explicitly unavailable.
"""
from datetime import datetime, timezone


METRICS = {
    "staff": ("scheduled_staff", "clocked_in_staff"),
    "orders": ("accepted_orders", "accepted_order_value", "captured_revenue"),
    "kitchen": ("open_tickets",),
    "tables": ("occupied_tables",),
    "reservations": ("upcoming_reservations", "seated_reservations"),
}


def compose_dashboard(*, principal, as_of, snapshots):
    if not getattr(principal, "authenticated", False) or getattr(principal, "role", None) not in ("manager", "owner"):
        raise PermissionError("manager authorization required")
    venue = getattr(principal, "venue_id", None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError("trusted venue required")
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("aware as_of required")
    if not isinstance(snapshots, dict) or set(snapshots) - set(METRICS):
        raise ValueError("unknown dashboard source")
    instant = as_of.astimezone(timezone.utc).isoformat()
    output = {}
    for domain, keys in METRICS.items():
        source = snapshots.get(domain)
        if source is not None:
            if not isinstance(source, dict) or source.get("venue_id") != venue or source.get("as_of_utc") != instant or source.get("is_live") is True:
                raise ValueError("mismatched or untrusted snapshot")
        for key in keys:
            value = source.get(key) if source is not None else None
            if value is None:
                output[key] = {"status": "unavailable", "value": None}
            elif not isinstance(value, dict) or value.get("status") not in ("available", "unavailable") or (value["status"] == "unavailable" and value.get("value", value.get("value_cents")) is not None):
                raise ValueError("invalid KPI state")
            else:
                output[key] = dict(value)
    return {"venue_id": venue, "as_of_utc": instant, "is_live": False,
            "source": "offline_trusted_snapshots", "metrics": output}


if __name__ == "__main__":
    import unittest
    from types import SimpleNamespace

    class ContractTests(unittest.TestCase):
        def setUp(self):
            self.principal = SimpleNamespace(authenticated=True, role="manager", venue_id="fictional-a")
            self.now = datetime(2026, 11, 28, 7, tzinfo=timezone.utc)

        def test_missing_is_not_zero(self):
            result = compose_dashboard(principal=self.principal, as_of=self.now, snapshots={})
            self.assertIsNone(result["metrics"]["clocked_in_staff"]["value"])
            self.assertEqual(result["metrics"]["captured_revenue"]["status"], "unavailable")
            self.assertFalse(result["is_live"])

        def test_trusted_source(self):
            snap = {"venue_id": "fictional-a", "as_of_utc": self.now.isoformat(),
                    "accepted_orders": {"status": "available", "value": 2}, "is_live": False}
            result = compose_dashboard(principal=self.principal, as_of=self.now, snapshots={"orders": snap})
            self.assertEqual(result["metrics"]["accepted_orders"]["value"], 2)

        def test_tenant_and_time_rejected(self):
            for change in ({"venue_id": "fictional-b"}, {"as_of_utc": "2026-11-27T07:00:00+00:00"}, {"is_live": True}):
                snap = {"venue_id": "fictional-a", "as_of_utc": self.now.isoformat(), "is_live": False, **change}
                with self.assertRaises(ValueError):
                    compose_dashboard(principal=self.principal, as_of=self.now, snapshots={"orders": snap})

        def test_manager_gate(self):
            with self.assertRaises(PermissionError):
                compose_dashboard(principal=SimpleNamespace(authenticated=True, role="staff", venue_id="fictional-a"), as_of=self.now, snapshots={})

    unittest.main()
