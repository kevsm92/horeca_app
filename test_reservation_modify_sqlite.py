import sqlite3
import unittest
from reservation_modify_sqlite import modify_reservation, ModificationConflict

class ModificationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.db.executescript("""CREATE TABLE tables(venue TEXT,id TEXT,capacity INTEGER,PRIMARY KEY(venue,id));
        CREATE TABLE bookings(venue TEXT,id TEXT,table_id TEXT,party INTEGER,start_us INTEGER,
        end_us INTEGER,turnover_us INTEGER,status TEXT,revision INTEGER,PRIMARY KEY(venue,id));
        INSERT INTO tables VALUES('a','t1',4),('a','t2',2),('b','t1',8);
        INSERT INTO bookings VALUES('a','r1','t1',2,100,200,20,'confirmed',3);
        INSERT INTO bookings VALUES('a','r2','t2',2,300,400,20,'confirmed',0);
        INSERT INTO bookings VALUES('b','r1','t1',2,100,200,20,'confirmed',3);""")
    def tearDown(self):
        self.db.close()
    def modify(self, **kw):
        args=dict(venue='a',booking_id='r1',expected_revision=3,table_id='t1',party=2,
                  start_us=500,end_us=600,turnover_us=20)
        args.update(kw)
        return modify_reservation(self.db,**args)
    def state(self):
        return self.db.execute("SELECT table_id,party,start_us,end_us,revision FROM bookings WHERE venue='a' AND id='r1'").fetchone()
    def test_success_and_revision(self):
        self.assertEqual(self.modify(table_id='t2'),4)
        self.assertEqual(self.state(),('t2',2,500,600,4))
    def test_cross_venue_no_mutation(self):
        with self.assertRaises(ModificationConflict): self.modify(venue='c')
        self.assertEqual(self.state(),('t1',2,100,200,3))
    def test_stale_revision(self):
        with self.assertRaises(ModificationConflict): self.modify(expected_revision=2)
    def test_capacity_and_rollback(self):
        with self.assertRaises(ModificationConflict): self.modify(table_id='t2',party=3)
        self.assertEqual(self.state(),('t1',2,100,200,3))
    def test_turnover_overlap(self):
        with self.assertRaises(ModificationConflict): self.modify(table_id='t2',start_us=280,end_us=290)
        self.assertEqual(self.modify(table_id='t2',start_us=280,end_us=281,turnover_us=19),4)
    def test_seated_immutable(self):
        self.db.execute("UPDATE bookings SET status='seated' WHERE venue='a' AND id='r1'")
        with self.assertRaises(ModificationConflict): self.modify()
    def test_invalid_and_nested(self):
        for kwargs in ({'party':True},{'end_us':500},{'turnover_us':-1}):
            with self.assertRaises(ValueError): self.modify(**kwargs)
        self.db.execute('BEGIN')
        with self.assertRaises(ValueError): self.modify()
        self.db.rollback()

if __name__=='__main__': unittest.main()
