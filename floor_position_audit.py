"""Offline SQLite move audit for synthetic floor-plan CAS prototype.

Install after prototypes.sqlite_floorplan_cas.init(db). Not a production migration,
authentication boundary, or protection against privileged database administrators.
"""
import sqlite3
import unittest


def install_audit(db):
    """Append move provenance and reject edits/deletes of audit rows."""
    db.executescript("""
        CREATE TABLE IF NOT EXISTS position_move_audit (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            venue TEXT NOT NULL, plan TEXT NOT NULL, table_id TEXT NOT NULL,
            old_x INTEGER NOT NULL, old_y INTEGER NOT NULL,
            new_x INTEGER NOT NULL, new_y INTEGER NOT NULL,
            old_revision INTEGER NOT NULL, new_revision INTEGER NOT NULL,
            recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE TRIGGER IF NOT EXISTS position_audit_immutable_update
        BEFORE UPDATE ON position_move_audit BEGIN
            SELECT RAISE(ABORT, 'audit events are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS position_audit_immutable_delete
        BEFORE DELETE ON position_move_audit BEGIN
            SELECT RAISE(ABORT, 'audit events are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS position_move_audit_insert
        AFTER UPDATE OF x, y, revision ON positions
        WHEN NEW.x != OLD.x OR NEW.y != OLD.y
        BEGIN
            SELECT CASE WHEN NEW.revision != OLD.revision + 1
                THEN RAISE(ABORT, 'move revision must increment once') END;
            INSERT INTO position_move_audit
                (venue, plan, table_id, old_x, old_y, new_x, new_y,
                 old_revision, new_revision)
            VALUES (OLD.venue, OLD.plan, OLD.table_id, OLD.x, OLD.y,
                    NEW.x, NEW.y, OLD.revision, NEW.revision);
        END;
    """)


class AuditTests(unittest.TestCase):
    def setUp(self):
        from prototypes.sqlite_floorplan_cas import init, save
        self.save = save
        self.db = sqlite3.connect(':memory:')
        init(self.db)
        install_audit(self.db)
        self.db.execute("INSERT INTO positions VALUES ('v1','room','T1',10,20,0)")
        self.db.execute("INSERT INTO positions VALUES ('v2','room','T1',50,60,0)")

    def tearDown(self):
        self.db.close()

    def events(self):
        return self.db.execute(
            'SELECT venue, old_x, new_x, old_revision, new_revision '
            'FROM position_move_audit ORDER BY event_id'
        ).fetchall()

    def test_successful_move_records_old_and_new_revision(self):
        self.assertEqual(self.save(self.db, 'v1','room','T1',0,30,40,100,100), 1)
        self.assertEqual(self.events(), [('v1',10,30,0,1)])

    def test_stale_and_wrong_venue_leave_no_audit(self):
        for venue, rev in [('v1',1), ('v3',0)]:
            with self.assertRaises(ValueError):
                self.save(self.db, venue,'room','T1',rev,30,40,100,100)
        self.assertEqual(self.events(), [])

    def test_unchanged_coordinates_not_logged(self):
        self.save(self.db,'v1','room','T1',0,10,20,100,100)
        self.assertEqual(self.events(), [])

    def test_audit_immutable(self):
        self.save(self.db,'v1','room','T1',0,30,40,100,100)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('DELETE FROM position_move_audit')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('UPDATE position_move_audit SET new_x=999')
        self.assertEqual(len(self.events()), 1)

    def test_invalid_revision_jump_rolls_back(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE positions SET x=33, revision=9 WHERE venue='v1'")
        self.assertEqual(
            self.db.execute("SELECT x,revision FROM positions WHERE venue='v1'").fetchone(),
            (10,0)
        )
        self.assertEqual(self.events(), [])

    def test_venue_scope_preserved_in_events(self):
        self.save(self.db,'v2','room','T1',0,70,60,100,100)
        self.assertEqual(self.events(), [('v2',50,70,0,1)])


if __name__ == '__main__':
    unittest.main()
