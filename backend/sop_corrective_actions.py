"""Offline append-only corrective actions for failed SOP inspections.

Authorization and venue identity must be supplied by a trusted service layer.
This module never changes an inspection outcome or certifies compliance.
"""
import uuid
from datetime import datetime, timezone
from backend.sop_inspections import initialize as initialize_inspections


def initialize(db):
    db.execute('PRAGMA foreign_keys=ON')
    initialize_inspections(db)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS sop_corrective_actions (
      venue_id TEXT NOT NULL, action_id TEXT NOT NULL,
      inspection_id TEXT NOT NULL, actor_id TEXT NOT NULL,
      description TEXT NOT NULL, recorded_at TEXT NOT NULL,
      PRIMARY KEY (venue_id,action_id),
      FOREIGN KEY (venue_id,inspection_id)
        REFERENCES sop_inspections(venue_id,inspection_id));
    CREATE TRIGGER IF NOT EXISTS corrective_no_update
      BEFORE UPDATE ON sop_corrective_actions
      BEGIN SELECT RAISE(ABORT,'immutable corrective action'); END;
    CREATE TRIGGER IF NOT EXISTS corrective_no_delete
      BEFORE DELETE ON sop_corrective_actions
      BEGIN SELECT RAISE(ABORT,'immutable corrective action'); END;
    """)


def record_action(db, *, venue_id, inspection_id, actor_id, description):
    if not all(isinstance(x,str) and x.strip() for x in
               (venue_id,inspection_id,actor_id,description)):
        raise ValueError('nonempty fields required')
    db.execute('PRAGMA foreign_keys=ON')
    action_id = str(uuid.uuid4())
    with db:
        outcome = db.execute(
            'SELECT outcome FROM sop_inspections WHERE venue_id=? AND inspection_id=?',
            (venue_id,inspection_id)).fetchone()
        if outcome is None:
            raise ValueError('inspection not found in venue')
        if outcome[0] == 'pass':
            raise ValueError('corrective action requires a deviation')
        db.execute("""INSERT INTO sop_corrective_actions
            (venue_id,action_id,inspection_id,actor_id,description,recorded_at)
            VALUES (?,?,?,?,?,?)""",
            (venue_id,action_id,inspection_id,actor_id,description,
             datetime.now(timezone.utc).isoformat()))
    return action_id


def list_actions(db, *, venue_id, inspection_id):
    if not venue_id or not inspection_id:
        raise ValueError('venue and inspection required')
    return db.execute("""SELECT action_id,actor_id,description,recorded_at
      FROM sop_corrective_actions WHERE venue_id=? AND inspection_id=?
      ORDER BY recorded_at,action_id""", (venue_id,inspection_id)).fetchall()
