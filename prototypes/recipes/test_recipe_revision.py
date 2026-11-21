import sqlite3
import unittest
from recipe_revision import initialize,publish,read

class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.executescript("""CREATE TABLE recipe_ingredients(venue_id TEXT,ingredient_id TEXT,unit TEXT,PRIMARY KEY(venue_id,ingredient_id));
          CREATE TABLE recipe_components(venue_id TEXT,recipe_id TEXT,ingredient_id TEXT,quantity INTEGER);""")
        self.db.executemany('INSERT INTO recipe_ingredients VALUES (?,?,?)',[('A','flour','mg'),('B','flour','mg')])
        self.db.executemany('INSERT INTO recipe_components VALUES (?,?,?,?)',[('A','bread','flour',100),('B','bread','flour',900)])
        initialize(self.db)
    def tearDown(self): self.db.close()
    def test_venue_isolation(self):
        publish(self.db,authorized_venue_id='A',recipe_id='bread',revision=1)
        self.assertIsNone(read(self.db,authorized_venue_id='B',recipe_id='bread',revision=1))
        self.assertEqual(read(self.db,authorized_venue_id='A',recipe_id='bread',revision=1)[0]['quantity'],100)
    def test_snapshot_does_not_change_with_live_bom(self):
        publish(self.db,authorized_venue_id='A',recipe_id='bread',revision=1)
        self.db.execute('UPDATE recipe_components SET quantity=200 WHERE venue_id=?',('A',))
        self.assertEqual(read(self.db,authorized_venue_id='A',recipe_id='bread',revision=1)[0]['quantity'],100)
        publish(self.db,authorized_venue_id='A',recipe_id='bread',revision=2)
        self.assertEqual(read(self.db,authorized_venue_id='A',recipe_id='bread',revision=2)[0]['quantity'],200)
    def test_duplicate_and_mutation_rejected(self):
        publish(self.db,authorized_venue_id='A',recipe_id='bread',revision=1)
        with self.assertRaises(sqlite3.IntegrityError):publish(self.db,authorized_venue_id='A',recipe_id='bread',revision=1)
        with self.assertRaises(sqlite3.IntegrityError):self.db.execute('UPDATE recipe_revision_snapshots SET bom_json=?',('[]',))
        with self.assertRaises(sqlite3.IntegrityError):self.db.execute('DELETE FROM recipe_revision_snapshots')
    def test_empty_and_invalid_revision_rejected(self):
        with self.assertRaises(ValueError):publish(self.db,authorized_venue_id='A',recipe_id='missing',revision=1)
        for rev in (0,True,'1'):
            with self.assertRaises(ValueError):publish(self.db,authorized_venue_id='A',recipe_id='bread',revision=rev)
    def test_no_cross_venue_leak_for_unknown(self):
        self.assertIsNone(read(self.db,authorized_venue_id='A',recipe_id='bread',revision=99))
        with self.assertRaises(ValueError):read(self.db,authorized_venue_id='',recipe_id='bread',revision=1)
if __name__=='__main__':unittest.main()
