"""Offline manager staff KPIs from trusted synthetic shifts and kiosk punch state.

The caller must authenticate the manager and load venue-scoped records. No HTTP
route, employee scoring, or inference of actual presence from scheduled shifts.
"""
from datetime import datetime, timezone


def manager_staff_kpis(*, principal, shifts, active_punches, as_of):
    if not getattr(principal, "authenticated", False) or getattr(principal, "role", None) not in ("manager", "owner"):
        raise PermissionError("manager authentication required")
    venue = getattr(principal, "venue_id", None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError("trusted venue required")
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("aware as_of required")
    now = as_of.astimezone(timezone.utc)
    scheduled = set()
    for shift in shifts:
        if shift["venue_id"] != venue:
            continue
        start, end = shift["start_utc"], shift["end_utc"]
        if any(not isinstance(x, datetime) or x.tzinfo is None or x.utcoffset() is None for x in (start, end)) or end <= start:
            raise ValueError("invalid shift interval")
        if start.astimezone(timezone.utc) <= now < end.astimezone(timezone.utc):
            scheduled.add(shift["staff_id"])
    present = None
    if active_punches is not None:
        present = set()
        for punch in active_punches:
            if punch["venue_id"] != venue:
                continue
            if punch.get("clocked_in") is True:
                present.add(punch["staff_id"])
            elif punch.get("clocked_in") is not False:
                raise ValueError("ambiguous punch state")
    return {
        "venue_id": venue, "as_of_utc": now.isoformat(), "source": "trusted_synthetic_inputs",
        "scheduled_staff": {"status": "available", "value": len(scheduled), "basis": "shift_intervals"},
        "clocked_in_staff": {"status": "unavailable", "value": None, "basis": "kiosk_punches"} if present is None else
            {"status": "available", "value": len(present), "basis": "kiosk_punches"},
        "attendance_inferred_from_schedule": False,
    }
