"""Offline manager-only draft shift edit; caller must persist with atomic revision CAS."""
from datetime import datetime, timezone


def prepare_shift_edit(*, principal, snapshot, expected_revision, shift_id, replacement, staff, stations):
    if not getattr(principal, "authenticated", False) or getattr(principal, "role", None) not in ("manager", "owner"):
        raise PermissionError("manager authentication required")
    venue = getattr(principal, "venue_id", None)
    if not isinstance(venue, str) or not venue.strip() or not isinstance(snapshot, dict) or snapshot.get("venue_id") != venue:
        raise PermissionError("trusted venue mismatch")
    revision = snapshot.get("revision")
    if type(revision) is not int or revision < 0 or type(expected_revision) is not int or revision != expected_revision:
        raise ValueError("invalid or stale revision")
    if snapshot.get("status") != "draft":
        raise ValueError("only draft rosters may be edited")
    shifts = snapshot.get("shifts")
    if not isinstance(shifts, list) or any(not isinstance(s, dict) or s.get("venue_id") != venue for s in shifts):
        raise ValueError("invalid or cross-venue shifts")
    if not isinstance(shift_id, str) or not shift_id.strip() or sum(s.get("id") == shift_id for s in shifts) != 1:
        raise ValueError("shift must exist exactly once")
    if not isinstance(replacement, dict) or replacement.get("id") != shift_id or replacement.get("venue_id") != venue:
        raise ValueError("replacement identity or venue mismatch")
    if replacement.get("staff_id") not in {s["id"] for s in staff if s.get("venue_id") == venue}:
        raise ValueError("unknown venue staff")
    if replacement.get("station") not in {s["id"] for s in stations if s.get("venue_id") == venue}:
        raise ValueError("unknown venue station")
    start, end = replacement.get("start_utc"), replacement.get("end_utc")
    if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None for t in (start, end)) or end <= start:
        raise ValueError("valid timezone-aware interval required")
    for s in shifts:
        if s["id"] == shift_id or s.get("staff_id") != replacement["staff_id"]:
            continue
        other_start, other_end = s.get("start_utc"), s.get("end_utc")
        if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None for t in (other_start, other_end)):
            raise ValueError("invalid existing shift interval")
        if start < other_end and other_start < end:
            raise ValueError("staff shift overlap")
    updated = dict(replacement, start_utc=start.astimezone(timezone.utc).isoformat(),
                   end_utc=end.astimezone(timezone.utc).isoformat())
    return {"venue_id": venue, "status": "draft", "expected_revision": revision,
            "next_revision": revision + 1, "requires_atomic_compare_and_swap": True,
            "shifts": [updated if s["id"] == shift_id else dict(s) for s in shifts]}
