"""Offline manager reservation KPI; trusted synthetic snapshots only, never live occupancy."""
from datetime import datetime, timezone

def reservation_kpis(*, principal, reservations, as_of):
    if not getattr(principal, "authenticated", False) or getattr(principal, "role", None) not in ("manager", "owner"):
        raise PermissionError("manager authentication required")
    venue = getattr(principal, "venue_id", None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError("trusted venue required")
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("aware as_of required")
    now = as_of.astimezone(timezone.utc)
    if reservations is None:
        upcoming = seated = None
        source = "not_connected"
    else:
        seen = set()
        upcoming = seated = 0
        for record in reservations:
            if not isinstance(record, dict):
                raise ValueError("invalid reservation record")
            if record.get("venue_id") != venue:
                continue
            rid, state, starts = (record.get(k) for k in ("id", "status", "starts_at"))
            if not isinstance(rid, str) or not rid.strip() or rid in seen:
                raise ValueError("invalid or duplicate reservation ID")
            seen.add(rid)
            if state not in ("confirmed", "seated", "completed", "cancelled", "no_show"):
                raise ValueError("invalid reservation status")
            if not isinstance(starts, datetime) or starts.tzinfo is None or starts.utcoffset() is None:
                raise ValueError("aware reservation start required")
            if state == "confirmed" and starts.astimezone(timezone.utc) >= now:
                upcoming += 1
            if state == "seated":
                if starts.astimezone(timezone.utc) > now:
                    raise ValueError("future seated reservation")
                seated += 1
        source = "trusted_reservation_records"
    def metric(value):
        return {"status": "unavailable" if value is None else "available", "value": value}
    return {"venue_id": venue, "as_of_utc": now.isoformat(), "source": source,
            "upcoming_reservations": metric(upcoming), "seated_reservations": metric(seated),
            "is_live": False}
