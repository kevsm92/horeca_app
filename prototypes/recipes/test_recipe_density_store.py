import sqlite3
import unittest
from recipe_density_store import (initialize_density_store, append_density_revision,
                                  latest_approved_density)


class DensityStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize_density_store(self.db)
        self.args = dict(authorized_venue='fictional-a', ingredient_id='fictional-oil',
                         revision=1, status='approved', mg_per_ml_numerator=900,
                         mg_per_ml_denominator=1)

    def tearDown(self):
        self.db.close()

    def test_approved_lookup_and_tenant_isolation(self):
        append_density_revision(self.db, **self.args)
        self.assertEqual(latest_approved_density(self.db, authorized_venue='fictional-a',
                         ingredient_id='fictional-oil')['revision'], 1)
        self.assertIsNone(latest_approved_density(self.db, authorized_venue='fictional-b',
                          ingredient_id='fictional-oil'))
        self.assertIsNone(latest_approved_density(self.db, authorized_venue='fictional-a',
                          ingredient_id='fictional-milk'))

    def test_revocation_disables_latest_without_erasing_history(self):
        append_density_revision(self.db, **self.args)
        append_density_revision(self.db, **{**self.args, 'revision': 2, 'status': 'revoked'})
        self.assertIsNone(latest_approved_density(self.db, authorized_venue='fictional-a',
                          ingredient_id='fictional-oil'))
        self.assertEqual(self.db.execute('SELECT count(*) FROM ingredient_density_revisions').fetchone()[0], 2)

    def test_duplicate_and_skipped_revision_rejected(self):
        append_density_revision(self.db, **self.args)
        for revision in (1, 3):
            with self.assertRaises(ValueError):
                append_density_revision(self.db, **{**self.args, 'revision': revision})

    def test_immutable_database_triggers(self):
        append_density_revision(self.db, **self.args)
        for statement in ('UPDATE ingredient_density_revisions SET status="revoked"',
                          'DELETE FROM ingredient_density_revisions'):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(statement)

    def test_invalid_inputs(self):
        for patch in ({'revision': True}, {'mg_per_ml_numerator': 0},
                      {'mg_per_ml_denominator': 1.5}, {'status': 'pending'},
                      {'authorized_venue': ''}, {'ingredient_id': ''}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                append_density_revision(self.db, **{**self.args, **patch})

    def test_venue_independent_revision_sequences(self):
        append_density_revision(self.db, **self.args)
        append_density_revision(self.db, **{**self.args, 'authorized_venue': 'fictional-b'})
        self.assertEqual(self.db.execute('SELECT count(*) FROM ingredient_density_revisions').fetchone()[0], 2)


if __name__ == '__main__':
    unittest.main()
