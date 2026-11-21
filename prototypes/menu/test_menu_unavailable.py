"""Regression tests for fail-closed SQLite failures in the read-only menu API."""
import json
import sqlite3
import unittest
from wsgiref.util import setup_testing_defaults

from menu_catalog import connect
from menu_http import make_menu_app


class MenuUnavailableTests(unittest.TestCase):
    def call(self, db, resolver):
        env = {}
        setup_testing_defaults(env)
        env.update(PATH_INFO='/api/v1/menu-items', REQUEST_METHOD='GET')
        captured = {}

        def start(status, headers):
            captured['status'] = status
            captured['headers'] = dict(headers)

        body = json.loads(b''.join(make_menu_app(db, resolver)(env, start)))
        return captured, body

    def test_closed_catalog_returns_sanitized_503(self):
        db = connect(':memory:')
        db.close()
        meta, body = self.call(db, lambda _: {'venue_id': 'demo', 'permissions': {'menu:read'}})
        self.assertEqual(meta['status'], '503 Service Unavailable')
        self.assertEqual(body, {'error': 'temporarily_unavailable'})
        self.assertEqual(meta['headers']['Cache-Control'], 'no-store')

    def test_session_database_failure_returns_sanitized_503(self):
        db = connect(':memory:')

        def failed(_):
            raise sqlite3.OperationalError('sensitive db path')

        meta, body = self.call(db, failed)
        self.assertEqual(meta['status'], '503 Service Unavailable')
        self.assertNotIn('sensitive', json.dumps(body))
        db.close()

    def test_missing_identity_remains_401(self):
        db = connect(':memory:')
        meta, body = self.call(db, lambda _: None)
        self.assertEqual(meta['status'], '401 Unauthorized')
        self.assertEqual(body, {'error': 'unauthenticated'})
        db.close()


if __name__ == '__main__':
    unittest.main()
