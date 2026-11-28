import sqlite3
import unittest
from menu_recipe_revision_gate import resolve_published_recipe

class GateTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.executescript('''CREATE TABLE menu_recipe_links(venue_id TEXT,item_id TEXT,recipe_id TEXT,recipe_revision INTEGER);
        CREATE TABLE recipe_revision_snapshots(venue_id TEXT,recipe_id TEXT,revision INTEGER,bom_json TEXT);''')
        self.db.executemany('INSERT INTO menu_recipe_links VALUES (?,?,?,?)', [('A','soup','r',2),('B','soup','r',2),('A','stale','r',3)])
        self.db.executemany('INSERT INTO recipe_revision_snapshots VALUES (?,?,?,?)', [('A','r',2,'[{"ingredient_id":"demo","quantity":10,"unit":"mg"}]'),('B','r',2,'[{"ingredient_id":"other","quantity":20,"unit":"mg"}]')])
    def tearDown(self): self.db.close()
    def test_venue_isolation(self):
        self.assertEqual(resolve_published_recipe(self.db,authorized_venue_id='A',item_id='soup')['bom'][0]['ingredient_id'],'demo')
        self.assertEqual(resolve_published_recipe(self.db,authorized_venue_id='B',item_id='soup')['bom'][0]['ingredient_id'],'other')
    def test_missing_link(self):
        self.assertIsNone(resolve_published_recipe(self.db,authorized_venue_id='B',item_id='stale'))
    def test_unpublished_revision_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'not published'):
            resolve_published_recipe(self.db,authorized_venue_id='A',item_id='stale')
    def test_invalid_identity(self):
        for venue,item in [('', 'soup'),('A',''),(None,'soup')]:
            with self.assertRaises(ValueError): resolve_published_recipe(self.db,authorized_venue_id=venue,item_id=item)
    def test_no_certification(self):
        value=resolve_published_recipe(self.db,authorized_venue_id='A',item_id='soup')
        self.assertEqual((value['allergen_status'],value['cost_status']),('unverified','not_quoted'))

    def test_invalid_published_bom_rejected(self):
        invalid = ['not-json', '[]', '[{"ingredient_id":"demo","quantity":0,"unit":"mg"}]',
                   '[{"ingredient_id":"demo","quantity":10,"unit":"kg"}]',
                   '[{"ingredient_id":"demo","quantity":10,"unit":"mg"},{"ingredient_id":"demo","quantity":2,"unit":"mg"}]']
        for payload in invalid:
            with self.subTest(payload=payload):
                self.db.execute('UPDATE recipe_revision_snapshots SET bom_json=? WHERE venue_id=?', (payload,'A'))
                with self.assertRaises(ValueError):
                    resolve_published_recipe(self.db,authorized_venue_id='A',item_id='soup')
                self.assertEqual(resolve_published_recipe(self.db,authorized_venue_id='B',item_id='soup')['bom'][0]['ingredient_id'],'other')

if __name__=='__main__': unittest.main()
