"""Offline manager verification of corrective-action rechecks (not certification).

The trusted caller must authenticate and authorize manager_id for venue_id.
Verification never changes an original inspection or its failed outcome.
"""
import uuid
from datetime import datetime, timezone
from backend.sop_rechecks import initialize as initialize_rechecks


def initialize(db):
    db.execute('PRAGMA foreign_keys=ON')
    initialize_rechecks(db)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS sop_manager_verifications (
      venue_id TEXT NOT NULL, verification_id TEXT NOT NULL,
      recheck_id TEXT NOT NULL, manager_id TEXT NOT NULL,
      decision TEXT NOT NULL CHECK(decision IN ('verified','rejected')),
      note TEXT NOT NULL CHECK(length(trim(note))>0), verified_at TEXT NOT NULL,
      PRIMARY KEY(venue_id,verification_id),
      UNIQUE(venue_id,recheck_id),
      FOREIGN KEY(venue_id,recheck_id) REFERENCES sop_rechecks(venue_id,recheck_id));
    CREATE TRIGGER IF NOT EXISTS verification_no_update BEFORE UPDATE ON sop_manager_verifications
      BEGIN SELECT RAISE(ABORT,'immutable verification'); END;
    CREATE TRIGGER IF NOT EXISTS verification_no_delete BEFORE DELETE ON sop_manager_verifications
      BEGIN SELECT RAISE(ABORT,'immutable verification'); END;
    """)


def verify_recheck(db, *, venue_id, recheck_id, manager_id, decision, note):
    if not all(isinstance(v,str) and v.strip() for v in (venue_id,recheck_id,manager_id,note)):
        raise ValueError('required fields missing')
    if decision not in ('verified','rejected'):
        raise ValueError('invalid decision')
    db.execute('PRAGMA foreign_keys=ON')
    with db:
        evidence=db.execute("""SELECT r.linked_by, i.actor_id, i.outcome
          FROM sop_rechecks r JOIN sop_inspections i
          ON i.venue_id=r.venue_id AND i.inspection_id=r.recheck_inspection_id
          WHERE r.venue_id=? AND r.recheck_id=?""",(venue_id,recheck_id)).fetchone()
        if not evidence:
            raise ValueError('recheck not found in venue')
        if manager_id in evidence[:2]:
            raise ValueError('independent manager verification required')
        if decision == 'verified' and evidence[2] != 'pass':
            raise ValueError('only a passing recheck may be verified')
        key=str(uuid.uuid4())
        db.execute("""INSERT INTO sop_manager_verifications VALUES (?,?,?,?,?,?,?)""",
                   (venue_id,key,recheck_id,manager_id,decision,note,
                    datetime.now(timezone.utc).isoformat()))
    return key
