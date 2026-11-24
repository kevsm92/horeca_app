"""Append-only SOP revision acknowledgements, not evidence of physical inspection.

Caller must authenticate and authorize the actor and venue before invoking.
"""
from datetime import datetime
from backend.sop_revisions import initialize as initialize_revisions


def initialize(db):
    initialize_revisions(db)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS sop_acknowledgements (
      venue_id TEXT NOT NULL,
      sop_id TEXT NOT NULL,
      revision INTEGER NOT NULL CHECK(revision > 0),
      actor_id TEXT NOT NULL CHECK(length(trim(actor_id)) > 0),
      acknowledged_at TEXT NOT NULL,
      PRIMARY KEY (venue_id, sop_id, revision, actor_id),
      FOREIGN KEY (venue_id, sop_id, revision)
        REFERENCES sop_revisions(venue_id, sop_id, revision)
    );
    CREATE TRIGGER IF NOT EXISTS sop_ack_no_update
      BEFORE UPDATE ON sop_acknowledgements
      BEGIN SELECT RAISE(ABORT, 'immutable acknowledgement'); END;
    CREATE TRIGGER IF NOT EXISTS sop_ack_no_delete
      BEFORE DELETE ON sop_acknowledgements
      BEGIN SELECT RAISE(ABORT, 'immutable acknowledgement'); END;
    """)


def acknowledge(db, *, venue_id, sop_id, revision, actor_id, acknowledged_at):
    """Record a single actor's acknowledgement of a specific approved revision.

    Reject duplicate submissions and unapproved/cross-venue revisions. This is
    not a completed check, measurement, manager verification or certification.
    """
    if not all(isinstance(v, str) and v.strip() for v in
               (venue_id, sop_id, actor_id, acknowledged_at)):
        raise ValueError("nonempty identity and timestamp required")
    if type(revision) is not int or revision < 1:
        raise ValueError("positive integer revision required")
    try:
        stamp = datetime.fromisoformat(acknowledged_at)
    except ValueError as exc:
        raise ValueError("valid ISO timestamp required") from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("timezone-aware timestamp required")
    db.execute("PRAGMA foreign_keys=ON")
    with db:
        db.execute(
            "INSERT INTO sop_acknowledgements VALUES (?,?,?,?,?)",
            (venue_id, sop_id, revision, actor_id, stamp.isoformat()),
        )


def list_acknowledgements(db, *, venue_id, sop_id, revision):
    if not venue_id or not sop_id or type(revision) is not int or revision < 1:
        raise ValueError("venue, SOP and revision required")
    return db.execute(
        "SELECT actor_id, acknowledged_at FROM sop_acknowledgements "
        "WHERE venue_id=? AND sop_id=? AND revision=? ORDER BY actor_id",
        (venue_id, sop_id, revision),
    ).fetchall()
