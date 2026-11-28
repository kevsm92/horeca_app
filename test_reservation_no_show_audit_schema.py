import sqlite3
import unittest
from reservation_no_show_audit_schema import install

class AuditSchemaTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        install(self.db)
        self.row = ('event-1','venue-a','booking-1','staff-1','2026-11-16T19:56:00+00:00',0,1,'confirmed','no_show')
    def tearDown(self):
        self.db.close()
    def insert(self, row=None):
        self.db.execute('INSERT INTO reservation_no_show_audit VALUES (?,?,?,?,?,?,?,?,?)', row or self.row)
    def test_valid_event_and_idempotent_schema_install(self):
        install(self.db)
        self.insert()
        self.assertEqual(self.db.execute('SELECT count(*) FROM reservation_no_show_audit').fetchone()[0],1)
    def test_duplicate_revision_rejected(self):
        self.insert()
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert(('event-2',)+self.row[1:])
    def test_invalid_revision_or_transition_rejected(self):
        for idx, value in ((6,2),(7,'cancelled'),(3,''),(4,'')):
            row=list(self.row);row[idx]=value
            with self.assertRaises(sqlite3.IntegrityError): self.insert(tuple(row))
    def test_update_delete_rejected(self):
        self.insert()
        for sql in ('UPDATE reservation_no_show_audit SET actor_id="other"', 'DELETE FROM reservation_no_show_audit'):
            with self.assertRaises(sqlite3.IntegrityError): self.db.execute(sql)
    def test_venue_scoped_revision(self):
        self.insert()
        self.insert(('event-2','venue-b')+self.row[2:])
        self.assertEqual(self.db.execute('SELECT count(*) FROM reservation_no_show_audit').fetchone()[0],2)

if __name__=='__main__': unittest.main()
