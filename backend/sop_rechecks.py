"""Offline SOP deviation recheck links; authorization belongs to trusted caller."""
import uuid
from datetime import datetime, timezone
from backend.sop_corrective_actions import initialize as initialize_actions


def initialize(db):
    db.execute('PRAGMA foreign_keys=ON')
    initialize_actions(db)
    db.executescript('''
    CREATE TABLE IF NOT EXISTS sop_rechecks (
      venue_id TEXT NOT NULL, recheck_id TEXT NOT NULL,
      original_inspection_id TEXT NOT NULL, corrective_action_id TEXT NOT NULL,
      recheck_inspection_id TEXT NOT NULL, linked_by TEXT NOT NULL,
      linked_at TEXT NOT NULL,
      PRIMARY KEY(venue_id,recheck_id),
      UNIQUE(venue_id,recheck_inspection_id),
      FOREIGN KEY(venue_id,original_inspection_id) REFERENCES sop_inspections(venue_id,inspection_id),
      FOREIGN KEY(venue_id,corrective_action_id) REFERENCES sop_corrective_actions(venue_id,action_id),
      FOREIGN KEY(venue_id,recheck_inspection_id) REFERENCES sop_inspections(venue_id,inspection_id));
    CREATE TRIGGER IF NOT EXISTS rechecks_no_update BEFORE UPDATE ON sop_rechecks
      BEGIN SELECT RAISE(ABORT,'immutable recheck'); END;
    CREATE TRIGGER IF NOT EXISTS rechecks_no_delete BEFORE DELETE ON sop_rechecks
      BEGIN SELECT RAISE(ABORT,'immutable recheck'); END;
    ''')


def link_recheck(db, *, venue_id, original_inspection_id, corrective_action_id,
                 recheck_inspection_id, linked_by):
    if not all(isinstance(v, str) and v.strip() for v in
               (venue_id, original_inspection_id, corrective_action_id,
                recheck_inspection_id, linked_by)):
        raise ValueError('all identifiers required')
    if original_inspection_id == recheck_inspection_id:
        raise ValueError('recheck must be a distinct inspection')
    db.execute('PRAGMA foreign_keys=ON')
    with db:
        original = db.execute('''SELECT sop_id,revision,equipment_id,outcome,recorded_at
            FROM sop_inspections WHERE venue_id=? AND inspection_id=?''',
            (venue_id,original_inspection_id)).fetchone()
        recheck = db.execute('''SELECT sop_id,revision,equipment_id,outcome,recorded_at
            FROM sop_inspections WHERE venue_id=? AND inspection_id=?''',
            (venue_id,recheck_inspection_id)).fetchone()
        action = db.execute('''SELECT inspection_id,recorded_at FROM sop_corrective_actions
            WHERE venue_id=? AND action_id=?''',(venue_id,corrective_action_id)).fetchone()
        if not original or not recheck or not action:
            raise ValueError('missing venue-scoped evidence')
        if original[3] == 'pass' or action[0] != original_inspection_id:
            raise ValueError('action must address original deviation')
        if original[:3] != recheck[:3]:
            raise ValueError('recheck must match SOP revision and equipment')
        if not (original[4] < action[1] < recheck[4]):
            raise ValueError('recheck must follow corrective action')
        key = str(uuid.uuid4())
        db.execute('''INSERT INTO sop_rechecks VALUES (?,?,?,?,?,?,?)''',
                   (venue_id,key,original_inspection_id,corrective_action_id,
                    recheck_inspection_id,linked_by,datetime.now(timezone.utc).isoformat()))
    return key
