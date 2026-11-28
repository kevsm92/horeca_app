import sqlite3
import unittest
from recipe_density_provenance import density_approval_provenance as lookup


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute("""CREATE TABLE ingredient_density_revisions (
            venue_id TEXT, ingredient_id TEXT, revision INTEGER, status TEXT,
            mg_per_ml_numerator INTEGER, mg_per_ml_denominator INTEGER)""")

    def tearDown(self):
        self.db.close()

    def add(self, venue='a', revision=1, status='approved'):
        self.db.execute('INSERT INTO ingredient_density_revisions VALUES (?,?,?,?,?,?)',
                        (venue, 'oil', revision, status, 900, 1))

    def test_missing(self):
        self.assertEqual(lookup(self.db, authorized_venue='a', ingredient_id='oil')['reason'], 'missing')

    def test_latest_approved(self):
        self.add()
        self.add(revision=2)
        self.assertEqual(lookup(self.db, authorized_venue='a', ingredient_id='oil')['revision'], 2)

    def test_revoked(self):
        self.add()
        self.add(revision=2, status='revoked')
        self.assertFalse(lookup(self.db, authorized_venue='a', ingredient_id='oil')['usable'])

    def test_venue_isolation(self):
        self.add()
        self.assertEqual(lookup(self.db, authorized_venue='b', ingredient_id='oil')['reason'], 'missing')

    def test_invalid_context(self):
        with self.assertRaises(ValueError):
            lookup(self.db, authorized_venue='', ingredient_id='oil')
        with self.assertRaises(ValueError):
            lookup(self.db, authorized_venue='a', ingredient_id='')


if __name__ == '__main__':
    unittest.main()
