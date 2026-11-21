"""No-network bootstrap safety regressions (synthetic fixtures only)."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from local_bootstrap import open_existing_database, serve_local


class LocalBootstrapTests(unittest.TestCase):
    def test_missing_database_rejected_without_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'missing.sqlite'
            with self.assertRaises(ValueError):
                open_existing_database(str(path))
            self.assertFalse(path.exists())

    def test_relative_path_rejected(self):
        with self.assertRaises(ValueError):
            open_existing_database('relative.sqlite')

    def test_uninitialized_database_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'empty.sqlite'
            sqlite3.connect(path).close()
            with self.assertRaises(ValueError):
                open_existing_database(str(path))

    def test_valid_existing_schema_accepted_without_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'ready.sqlite'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE menu_items (item_id TEXT)')
                db.execute('CREATE TABLE menu_sessions (token_digest TEXT)')
            db = open_existing_database(str(path))
            try:
                self.assertEqual(db.execute('SELECT count(*) FROM menu_items').fetchone()[0], 0)
            finally:
                db.close()

    def test_non_loopback_rejected_before_database_or_listener(self):
        with patch('local_bootstrap.open_existing_database') as opener, patch('local_bootstrap.make_server') as listener:
            with self.assertRaises(ValueError):
                serve_local('/unused', host='0.0.0.0')
            opener.assert_not_called()
            listener.assert_not_called()

    def test_invalid_port_rejected_before_listener(self):
        with patch('local_bootstrap.open_existing_database') as opener:
            with self.assertRaises(ValueError):
                serve_local('/unused', port=-1)
            opener.assert_not_called()


if __name__ == '__main__':
    unittest.main()
