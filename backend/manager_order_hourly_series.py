"""Offline manager-only UTC hourly accepted-order series; not captured revenue."""
from datetime import datetime, timedelta, timezone

def accepted_order_hourly_series(*, principal, orders, start, end):
    if not getattr(principal, "authenticated", False) or getattr(principal, "role", None) not in ("manager", "owner"):
        raise PermissionError("manager authentication required")
    venue = getattr(principal, "venue_id", None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError("trusted venue required")
    for instant in (start, end):
        if not isinstance(instant, datetime) or instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("aware bounds required")
    first, last = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
    if any((first.minute, first.second, first.microsecond, last.minute, last.second, last.microsecond)):
        raise ValueError("UTC hour-aligned bounds required")
    hours = int((last - first).total_seconds() // 3600)
    if not 1 <= hours <= 168 or first + timedelta(hours=hours) != last:
        raise ValueError("range must be 1..168 whole hours")
    buckets = [{"hour_start_utc": (first + timedelta(hours=i)).isoformat(),
                "accepted_orders": None if orders is None else 0,
                "accepted_value_cents": None if orders is None else 0} for i in range(hours)]
    if orders is not None:
        seen = set()
        for record in orders:
            if not isinstance(record, dict) or record.get("venue_id") != venue:
                continue
            oid = record.get("id")
            if not isinstance(oid, str) or not oid or oid in seen:
                raise ValueError("invalid or duplicate order ID")
            seen.add(oid)
            status, cents, accepted_at = (record.get(k) for k in ("status", "total_cents", "accepted_at"))
            if status not in ("draft", "accepted", "cancelled") or type(cents) is not int or cents < 0:
                raise ValueError("invalid order")
            if status != "accepted":
                continue
            if not isinstance(accepted_at, datetime) or accepted_at.tzinfo is None or accepted_at.utcoffset() is None:
                raise ValueError("accepted order requires aware timestamp")
            stamp = accepted_at.astimezone(timezone.utc)
            if first <= stamp < last:
                index = int((stamp - first).total_seconds() // 3600)
                buckets[index]["accepted_orders"] += 1
                buckets[index]["accepted_value_cents"] += cents
    return {"venue_id": venue, "source": "trusted_order_records" if orders is not None else "not_connected",
            "status": "available" if orders is not None else "unavailable",
            "currency": "EUR", "is_live": False, "captured_revenue": None, "hours": buckets}
