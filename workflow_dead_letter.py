"""Explicit offline requeue of dead workflow events; no automatic external delivery."""
import sqlite3
from datetime import datetime, timezone


def requeue_dead(db: sqlite3.Connection, venue_id: str, event_key: str, now: datetime) -> bool:
    """Requeue one dead event only, preserving its attempt history and payload.

    Caller owns transaction and must authorize manager-level venue access upstream.
    """
    if not isinstance(venue_id, str) or not venue_id.strip() or not isinstance(event_key, str) or not event_key.strip():
        raise ValueError('venue and event key required')
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('timezone-aware timestamp required')
    result = db.execute("""UPDATE workflow_outbox
        SET status='pending', next_attempt_at=?
        WHERE venue_id=? AND event_key=? AND status='dead'""",
        (now.astimezone(timezone.utc).isoformat(), venue_id, event_key))
    return result.rowcount == 1
