"""Offline immutable SOP inspection records; caller enforces authorization."""
import uuid
from datetime import datetime, timezone
from backend.sop_revisions import initialize as initialize_revisions

def initialize(db):
    db.execute('PRAGMA foreign_keys=ON')
    initialize_revisions(db)
    db.executescript('''CREATE TABLE IF NOT EXISTS sop_inspections (
      venue_id TEXT NOT NULL, inspection_id TEXT NOT NULL,
      sop_id TEXT NOT NULL, revision INTEGER NOT NULL, actor_id TEXT NOT NULL,
      equipment_id TEXT NOT NULL, outcome TEXT NOT NULL
        CHECK(outcome IN ('pass','fail','not_performed')),
      measured_value TEXT, measured_unit TEXT, instrument_id TEXT,
      exception_note TEXT, recorded_at TEXT NOT NULL,
      PRIMARY KEY(venue_id,inspection_id),
      FOREIGN KEY(venue_id,sop_id,revision) REFERENCES sop_revisions(venue_id,sop_id,revision),
      CHECK ((measured_value IS NULL AND measured_unit IS NULL AND instrument_id IS NULL)
         OR (measured_value IS NOT NULL AND measured_unit IS NOT NULL AND instrument_id IS NOT NULL)),
      CHECK (outcome='pass' OR length(trim(coalesce(exception_note,'')))>0));
    CREATE TRIGGER IF NOT EXISTS inspection_immutable_update BEFORE UPDATE ON sop_inspections
      BEGIN SELECT RAISE(ABORT,'immutable inspection'); END;
    CREATE TRIGGER IF NOT EXISTS inspection_immutable_delete BEFORE DELETE ON sop_inspections
      BEGIN SELECT RAISE(ABORT,'immutable inspection'); END;''')

def record_check(db, *, venue_id, sop_id, revision, actor_id, equipment_id, outcome,
                 measured_value=None, measured_unit=None, instrument_id=None, exception_note=None):
    if not all(isinstance(v,str) and v.strip() for v in (venue_id,sop_id,actor_id,equipment_id)):
        raise ValueError('required identity missing')
    if type(revision) is not int or revision < 1 or outcome not in ('pass','fail','not_performed'):
        raise ValueError('invalid revision or outcome')
    measure=(measured_value,measured_unit,instrument_id)
    if any(v is not None for v in measure) and not all(isinstance(v,str) and v.strip() for v in measure):
        raise ValueError('complete measurement required')
    if outcome != 'pass' and not (isinstance(exception_note,str) and exception_note.strip()):
        raise ValueError('exception required')
    if exception_note is not None and not isinstance(exception_note,str):
        raise ValueError('invalid exception')
    key=str(uuid.uuid4())
    db.execute('PRAGMA foreign_keys=ON')
    with db:
        db.execute('INSERT INTO sop_inspections VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (venue_id,key,sop_id,revision,actor_id,equipment_id,outcome,
             measured_value,measured_unit,instrument_id,exception_note,
             datetime.now(timezone.utc).isoformat()))
    return key

def list_checks(db, *, venue_id, sop_id):
    if not all(isinstance(v,str) and v.strip() for v in (venue_id,sop_id)):
        raise ValueError('venue and SOP required')
    return db.execute('SELECT inspection_id,revision,actor_id,equipment_id,outcome,measured_value,measured_unit,instrument_id,exception_note,recorded_at FROM sop_inspections WHERE venue_id=? AND sop_id=? ORDER BY recorded_at,inspection_id',(venue_id,sop_id)).fetchall()
