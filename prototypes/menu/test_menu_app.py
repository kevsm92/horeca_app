"""End-to-end WSGI/SQLite session-to-catalog integration with fictional records."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from menu_app import make_authenticated_menu_app
from menu_catalog import connect, seed_synthetic
from menu_sessions import initialize_sessions, provision_test_session


class AuthenticatedMenuIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / 'menu.sqlite')
        initialize_sessions(self.db)
        seed_synthetic(self.db, venue_id='venue-a')
        seed_synthetic(self.db, venue_id='venue-b')
        self.db.execute("UPDATE menu_items SET price_cents=999 WHERE venue_id='venue-b' AND item_id='demo-food-1'")
        self.token = 'ab' * 32
        provision_test_session(self.db, token_hex=self.token, venue_id='venue-a', expires_at=2000)
        self.app = make_authenticated_menu_app(self.db, now=1000)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def call(self, cookie=None, query=''):
        environ = {}
        setup_testing_defaults(environ)
        environ.update(PATH_INFO='/api/v1/menu-items', REQUEST_METHOD='GET', QUERY_STRING=query)
        if cookie is not None:
            environ['HTTP_COOKIE'] = cookie
        response = {}
        def start_response(status, headers):
            response['status'] = status
            response['headers'] = dict(headers)
        body = b''.join(self.app(environ, start_response))
        return response['status'], json.loads(body), response['headers']

    def test_real_session_cookie_reads_only_its_venue(self):
        status, data, headers = self.call(f'horeca_session={self.token}')
        self.assertEqual(status, '200 OK')
        self.assertEqual(len(data['items']), 2)
        self.assertEqual(next(x['price_cents'] for x in data['items'] if x['kind'] == 'food'), 650)
        self.assertEqual(headers['Cache-Control'], 'no-store')

    def test_no_cookie_or_wrong_cookie_rejected(self):
        self.assertEqual(self.call()[0], '401 Unauthorized')
        self.assertEqual(self.call('horeca_session=' + 'cd' * 32)[0], '401 Unauthorized')

    def test_revoked_session_rejected(self):
        digest = hashlib.sha256(bytes.fromhex(self.token)).hexdigest()
        self.db.execute('UPDATE menu_sessions SET revoked_at=1000 WHERE token_digest=?', (digest,))
        self.assertEqual(self.call(f'horeca_session={self.token}')[0], '401 Unauthorized')

    def test_expired_session_rejected(self):
        digest = hashlib.sha256(bytes.fromhex(self.token)).hexdigest()
        self.db.execute('UPDATE menu_sessions SET expires_at=1000 WHERE token_digest=?', (digest,))
        self.assertEqual(self.call(f'horeca_session={self.token}')[0], '401 Unauthorized')

    def test_permission_denial(self):
        digest = hashlib.sha256(bytes.fromhex(self.token)).hexdigest()
        self.db.execute('UPDATE menu_sessions SET can_read_menu=0 WHERE token_digest=?', (digest,))
        self.assertEqual(self.call(f'horeca_session={self.token}')[0], '403 Forbidden')

    def test_query_cannot_select_other_venue(self):
        self.assertEqual(self.call(f'horeca_session={self.token}', 'venue_id=venue-b')[0], '400 Bad Request')

    def test_food_drink_filter(self):
        status, data, _ = self.call(f'horeca_session={self.token}', 'kind=drink')
        self.assertEqual(status, '200 OK')
        self.assertEqual([x['kind'] for x in data['items']], ['drink'])


if __name__ == '__main__':
    unittest.main()
