"""Read-only, venue-scoped offline outbox summary; caller authorizes venue."""
from datetime import datetime, timezone

STATES = ('pending', 'leased', 'delivered', 'dead_letter')


def queue_status(db, *, venue_id, now):
    """No payloads, event IDs, lease tokens, or staff data are returned."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('aware datetime required')
    instant = now.astimezone(timezone.utc).isoformat()
    counts = dict.fromkeys(STATES, 0)
    for state, count in db.execute("""SELECT state, COUNT(*) FROM workflow_outbox
        WHERE venue_id=? GROUP BY state""", (venue_id,)):
        if state not in counts:
            raise ValueError('unknown queue state')
        counts[state] = count
    actionable = db.execute("""SELECT COUNT(*) FROM workflow_outbox
        WHERE venue_id=? AND available_at_utc<=? AND
        (state='pending' OR (state='leased' AND lease_expires_at_utc<=?))""",
        (venue_id, instant, instant)).fetchone()[0]
    return {'counts': counts, 'actionable_now': actionable}
