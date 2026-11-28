"""Offline append-only receipts for synthetic roster publications.

Invoke after a successful roster snapshot compare-and-swap. The service boundary
must authenticate the principal and derive its venue and actor from the session.
"""
import json
from datetime import date, datetime, timezone


def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS roster_publication_receipts (
        venue_id TEXT NOT NULL, week_start TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK(revision > 0),
        actor_id TEXT NOT NULL, published_at TEXT NOT NULL,
        shift_ids_json TEXT NOT NULL,
        PRIMARY KEY (venue_id, week_start, revision))""")
    db.execute("""CREATE TRIGGER IF NOT EXISTS roster_receipt_no_update
        BEFORE UPDATE ON roster_publication_receipts
        BEGIN SELECT RAISE(ABORT, 'publication receipt immutable'); END""")
    db.execute("""CREATE TRIGGER IF NOT EXISTS roster_receipt_no_delete
        BEFORE DELETE ON roster_publication_receipts
        BEGIN SELECT RAISE(ABORT, 'publication receipt immutable'); END""")


def record_publication(db, *, principal, week_start, revision, published_at, shift_ids):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authorization required')
    venue = getattr(principal, 'venue_id', None)
    actor = getattr(principal, 'staff_id', None)
    if not isinstance(venue, str) or not venue.strip() or not isinstance(actor, str) or not actor.strip():
        raise PermissionError('trusted venue and actor required')
    try:
        week = date.fromisoformat(week_start)
    except (TypeError, ValueError):
        raise ValueError('invalid week') from None
    if week.weekday() != 0 or week.isoformat() != week_start:
        raise ValueError('Monday week required')
    if type(revision) is not int or revision <= 0:
        raise ValueError('positive revision required')
    if not isinstance(published_at, datetime) or published_at.tzinfo is None or published_at.utcoffset() is None:
        raise ValueError('aware timestamp required')
    if not isinstance(shift_ids, list) or any(not isinstance(s, str) or not s.strip() for s in shift_ids) or len(set(shift_ids)) != len(shift_ids):
        raise ValueError('unique shift IDs required')
    with db:
        db.execute('INSERT INTO roster_publication_receipts VALUES (?, ?, ?, ?, ?, ?)',
                   (venue, week_start, revision, actor, published_at.astimezone(timezone.utc).isoformat(), json.dumps(shift_ids)))
    return revision


def list_publications(db, *, principal, week_start):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authorization required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    return [dict(revision=r[0], actor_id=r[1], published_at=r[2], shift_ids=json.loads(r[3]))
            for r in db.execute('SELECT revision, actor_id, published_at, shift_ids_json FROM roster_publication_receipts WHERE venue_id=? AND week_start=? ORDER BY revision', (venue, week_start))]
