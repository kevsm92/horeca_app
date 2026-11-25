"""Offline, read-only review candidates for previously queued mock SOP tasks.

This is a manager-review queue, not an automatic notification or compliance verdict.
Caller must authorize venue access before invoking.
"""
from datetime import datetime, timezone


def pending_review_candidates(db, *, venue_id, as_of, limit=100):
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError('aware as_of required')
    if type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError('limit out of range')
    now = as_of.astimezone(timezone.utc).isoformat()
    # A pending task is never treated as a completed physical inspection.
    rows = db.execute('''SELECT t.event_id, t.check_id, t.sop_revision_id, o.created_at_utc
        FROM workflow_mock_tasks t JOIN workflow_outbox o
          ON o.event_id=t.event_id AND o.venue_id=t.venue_id
        WHERE t.venue_id=? AND t.status='open' AND o.state='delivered'
          AND o.created_at_utc<?
        ORDER BY o.created_at_utc, t.event_id LIMIT ?''', (venue_id, now, limit)).fetchall()
    return [dict(event_id=e, check_id=c, sop_revision_id=s, queued_at_utc=q,
                 review_required=True) for e,c,s,q in rows]
