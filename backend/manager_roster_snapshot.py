"""Authorized offline weekly roster read; no HTTP exposure."""
from datetime import date

def manager_roster_snapshot(*, principal, db, week_start):
    if not getattr(principal, "authenticated", False) or getattr(principal, "role", None) not in ("manager", "owner"):
        raise PermissionError("manager authorization required")
    venue = getattr(principal, "venue_id", None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError("trusted venue required")
    try:
        week = date.fromisoformat(week_start)
    except (TypeError, ValueError):
        raise ValueError("invalid week_start") from None
    if week.weekday() != 0 or week.isoformat() != week_start:
        raise ValueError("canonical Monday required")
    from roster_revision_store import read_snapshot
    stored = read_snapshot(db, venue_id=venue, week_start=week_start)
    if stored is None:
        return {"venue_id": venue, "week_start": week_start, "status": "missing", "revision": None, "shifts": [], "source": "persisted_roster"}
    payload = stored["payload"]
    if payload.get("venue_id") != venue or payload.get("status") not in ("draft", "published"):
        raise ValueError("invalid persisted roster")
    shifts = payload.get("shifts")
    if not isinstance(shifts, list) or any(not isinstance(s, dict) or s.get("venue_id") != venue for s in shifts):
        raise ValueError("invalid or cross-venue persisted shifts")
    return {"venue_id": venue, "week_start": week_start, "status": payload["status"],
            "revision": stored["revision"], "shifts": shifts, "source": "persisted_roster",
            "attendance": "not_inferred"}
