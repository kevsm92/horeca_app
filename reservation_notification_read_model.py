"""Read-only, venue-scoped projection of offline reservation notification intents.

The caller MUST authorize the requested venue before invoking this function.
No guest identifiers, delivery addresses or message bodies are exposed.
"""
import json


def list_mock_intents(conn, *, venue_id, limit=100):
    """Return a deterministic, bounded synthetic notification audit projection."""
    if type(venue_id) is not str or not venue_id.strip():
        raise ValueError('venue_id required')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be an integer between 1 and 100')
    rows = conn.execute(
        """SELECT event_id, kind, reservation_id, payload_json, state
           FROM reservation_notification_intents
           WHERE venue_id=? ORDER BY event_id LIMIT ?""", (venue_id, limit)
    ).fetchall()
    return [dict(event_id=event_id, kind=kind, reservation_id=reservation_id,
                 scheduled_utc=json.loads(payload)['scheduled_utc'], state=state)
            for event_id, kind, reservation_id, payload, state in rows]
