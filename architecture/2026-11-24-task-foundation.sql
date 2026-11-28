-- HORECA 2026-11-24: offline SQLite operational task foundation v1.
-- Synthetic-only prototype. Authentication/authorization MUST precede HTTP exposure.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS venue (id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS staff (venue_id TEXT NOT NULL, id TEXT NOT NULL, display_name TEXT NOT NULL, PRIMARY KEY (venue_id,id), FOREIGN KEY(venue_id) REFERENCES venue(id));
CREATE TABLE IF NOT EXISTS operational_task (
  venue_id TEXT NOT NULL, id TEXT NOT NULL, title TEXT NOT NULL CHECK(length(trim(title)) > 0),
  priority TEXT NOT NULL CHECK(priority IN ('low','normal','high','urgent')),
  status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','in_progress','completed','cancelled')),
  assignee_id TEXT, due_at TEXT, created_at TEXT NOT NULL,
  completed_at TEXT, completed_by TEXT,
  PRIMARY KEY (venue_id,id),
  FOREIGN KEY(venue_id) REFERENCES venue(id),
  FOREIGN KEY(venue_id,assignee_id) REFERENCES staff(venue_id,id),
  FOREIGN KEY(venue_id,completed_by) REFERENCES staff(venue_id,id),
  CHECK ((status='completed' AND completed_at IS NOT NULL AND completed_by IS NOT NULL) OR
         (status<>'completed' AND completed_at IS NULL AND completed_by IS NULL))
);
CREATE TABLE IF NOT EXISTS task_audit (
  sequence INTEGER PRIMARY KEY AUTOINCREMENT,
  venue_id TEXT NOT NULL, task_id TEXT NOT NULL, actor_id TEXT NOT NULL,
  action TEXT NOT NULL CHECK(action IN ('created','assigned','started','completed','cancelled','reopened')),
  occurred_at TEXT NOT NULL, details TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY(venue_id,task_id) REFERENCES operational_task(venue_id,id),
  FOREIGN KEY(venue_id,actor_id) REFERENCES staff(venue_id,id)
);
CREATE TRIGGER IF NOT EXISTS task_audit_no_update BEFORE UPDATE ON task_audit BEGIN SELECT RAISE(ABORT,'audit is append-only'); END;
CREATE TRIGGER IF NOT EXISTS task_audit_no_delete BEFORE DELETE ON task_audit BEGIN SELECT RAISE(ABORT,'audit is append-only'); END;
-- No automatic task status -> HACCP compliance conversion. SOP revision acknowledgement,
-- physical inspection measurements and manager verification are separate future entities.
-- Application transaction MUST update task and insert audit together; do not grant
-- arbitrary SQL clients direct write access. No proof of actor identity in this schema.
