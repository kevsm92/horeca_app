"""Offline immutable venue-scoped SOP revisions; no compliance certification."""
import hashlib
from datetime import datetime, timezone

def initialize(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS sop_revisions (
      venue_id TEXT NOT NULL, sop_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision > 0),
      author_id TEXT NOT NULL, approver_id TEXT NOT NULL,
      station TEXT NOT NULL, content TEXT NOT NULL, content_sha256 TEXT NOT NULL,
      approved_at TEXT NOT NULL,
      PRIMARY KEY(venue_id, sop_id, revision));
    CREATE TRIGGER IF NOT EXISTS sop_revision_no_update BEFORE UPDATE ON sop_revisions
      BEGIN SELECT RAISE(ABORT, 'immutable SOP revision'); END;
    CREATE TRIGGER IF NOT EXISTS sop_revision_no_delete BEFORE DELETE ON sop_revisions
      BEGIN SELECT RAISE(ABORT, 'immutable SOP revision'); END;
    """)

def approve_revision(db, *, venue_id, sop_id, author_id, approver_id, station, content,
                     expected_previous_revision):
    """Append only if expected predecessor matches; authorization is external."""
    if not all(isinstance(x, str) and x.strip() for x in
               (venue_id, sop_id, author_id, approver_id, station, content)):
        raise ValueError('nonempty SOP fields required')
    if author_id == approver_id:
        raise ValueError('independent approver required')
    if type(expected_previous_revision) is not int or expected_previous_revision < 0:
        raise ValueError('invalid expected revision')
    digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
    stamp = datetime.now(timezone.utc).isoformat()
    with db:
        current = db.execute('SELECT COALESCE(MAX(revision),0) FROM sop_revisions '
                             'WHERE venue_id=? AND sop_id=?', (venue_id, sop_id)).fetchone()[0]
        if current != expected_previous_revision:
            raise ValueError('stale SOP revision')
        revision = current + 1
        db.execute('INSERT INTO sop_revisions VALUES (?,?,?,?,?,?,?,?,?)',
                   (venue_id, sop_id, revision, author_id, approver_id, station,
                    content, digest, stamp))
    return revision

def get_revision(db, *, venue_id, sop_id, revision):
    if not venue_id or not sop_id or type(revision) is not int or revision < 1:
        raise ValueError('invalid lookup')
    return db.execute('SELECT revision,station,content,content_sha256,approved_at '
                      'FROM sop_revisions WHERE venue_id=? AND sop_id=? AND revision=?',
                      (venue_id, sop_id, revision)).fetchone()
