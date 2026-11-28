import sqlite3
import unittest
from menu_recipe_link import initialize, link_recipe, list_links

class MenuRecipeLinkTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('CREATE TABLE menu_items (venue_id TEXT NOT NULL,item_id TEXT NOT NULL,PRIMARY KEY(venue_id,item_id))')
        self.db.executemany('INSERT INTO menu_items VALUES (?,?)',[('A','soup'),('B','soup')])
        initialize(self.db)
    def tearDown(self): self.db.close()
    def test_isolated_venue_records(self):
        link_recipe(self.db,authorized_venue_id='A',item_id='soup',recipe_id='recipe-a',recipe_revision=1)
        link_recipe(self.db,authorized_venue_id='B',item_id='soup',recipe_id='recipe-b',recipe_revision=2)
        self.assertEqual(list_links(self.db,authorized_venue_id='A'),[{'item_id':'soup','recipe_id':'recipe-a','recipe_revision':1}])
        self.assertEqual(list_links(self.db,authorized_venue_id='B')[0]['recipe_id'],'recipe-b')
    def test_missing_or_cross_venue_item_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            link_recipe(self.db,authorized_venue_id='A',item_id='other',recipe_id='r',recipe_revision=1)
        self.assertEqual(list_links(self.db,authorized_venue_id='A'),[])
    def test_revision_update_is_explicit(self):
        for revision in (1,2):
            link_recipe(self.db,authorized_venue_id='A',item_id='soup',recipe_id='r',recipe_revision=revision)
        self.assertEqual(list_links(self.db,authorized_venue_id='A')[0]['recipe_revision'],2)
    def test_invalid_revision_rejected(self):
        for value in (0,-1,True,1.5,'1'):
            with self.assertRaises(ValueError):
                link_recipe(self.db,authorized_venue_id='A',item_id='soup',recipe_id='r',recipe_revision=value)
    def test_missing_identity_rejected(self):
        with self.assertRaises(ValueError):list_links(self.db,authorized_venue_id='')
        with self.assertRaises(ValueError):link_recipe(self.db,authorized_venue_id='',item_id='soup',recipe_id='r',recipe_revision=1)

if __name__=='__main__': unittest.main()
