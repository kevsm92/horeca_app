"""Synthetic WSGI contract tests; no network listener or external services."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from menu_catalog import initialize, seed_fictional
from menu_http import make_app


class MenuHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'menu.sqlite')
        with sqlite3.connect(self.path) as db:
            initialize(db)
            seed_fictional(db, 'a')
            seed_fictional(db, 'b')
        self.principal = {'venue_id': 'a', 'permissions': ['menu:read']}
        self.app = make_app(lambda: sqlite3.connect(self.path), lambda _: self.principal)

    def tearDown(self):
        self.temp.cleanup()

    def call(self, method='GET', path='/api/v1/menu-items', **headers):
        response = []
        body = b''.join(self.app({'REQUEST_METHOD': method, 'PATH_INFO': path, **headers},
                                 lambda status, h: response.append((status, dict(h)))))
        return response[0][0], response[0][1], json.loads(body)

    def test_authenticated_read_and_server_venue(self):
        status, headers, data = self.call(HTTP_X_VENUE_ID='b', QUERY_STRING='venue_id=b')
        self.assertEqual(status, '200 OK')
        self.assertEqual(len(data['items']), 2)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(data['items'][0]['currency'], 'EUR')

    def test_unauthenticated_and_forbidden(self):
        self.principal = None
        self.assertEqual(self.call()[0], '401 Unauthorized')
        self.principal = {'venue_id': 'a', 'permissions': []}
        self.assertEqual(self.call()[0], '403 Forbidden')
        self.principal = {'venue_id': '', 'permissions': ['menu:read']}
        self.assertEqual(self.call()[0], '403 Forbidden')

    def test_methods_and_paths_fail_closed(self):
        self.assertEqual(self.call(method='POST')[0], '405 Method Not Allowed')
        self.assertEqual(self.call(path='/api/v1/tables')[0], '404 Not Found')

    def test_db_failure_no_leak(self):
        self.app = make_app(lambda: sqlite3.connect(':memory:'), lambda _: self.principal)
        self.assertEqual(self.call()[2], {'error': 'catalog_unavailable'})

    def test_session_failure_no_leak(self):
        def fail(_):
            raise RuntimeError('private session detail')
        self.app = make_app(lambda: sqlite3.connect(self.path), fail)
        self.assertEqual(self.call()[2], {'error': 'session_unavailable'})


if __name__ == '__main__':
    unittest.main()
