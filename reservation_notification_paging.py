"""Keyset paging for offline reservation notification audit records.

Authorization of venue_id is mandatory at the caller boundary. No delivery occurs.
"""
import json


def page_mock_intents(conn, *, venue_id, after_event_id=None, limit=50):
    """Return (records, next_cursor), scoped to one previously authorized venue.

    Cursor is an opaque-to-client event identifier, not a security credential.
    Ordering is stable by event_id; only append-only event ledgers are supported.
    """
    if type(venue_id) is not str or not venue_id.strip():
        raise ValueError('venue_id required')
    if type(after_event_id) is not str and after_event_id is not None:
        raise ValueError('invalid cursor')
    if after_event_id == '':
        raise ValueError('invalid cursor')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be an integer between 1 and 100')
    rows = conn.execute(
        """SELECT event_id,kind,reservation_id,payload_json,state
           FROM reservation_notification_intents
           WHERE venue_id=? AND (? IS NULL OR event_id>?)
           ORDER BY event_id LIMIT ?""",
        (venue_id, after_event_id, after_event_id, limit + 1),
    ).fetchall()
    has_more = len(rows) > limit
    records = [dict(event_id=e, kind=k, reservation_id=r,
                    scheduled_utc=json.loads(p)['scheduled_utc'], state=s)
               for e,k,r,p,s in rows[:limit]]
    return records, (records[-1]['event_id'] if has_more else None)
