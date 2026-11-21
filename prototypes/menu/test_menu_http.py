import json
import tempfile
import unittest
from pathlib import Path
from wsgiref.util import setup_testing_defaults
from menu_catalog import connect, seed_synthetic
from menu_http import make_menu_app

class MenuHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / 'catalog.sqlite')
        seed_synthetic(self.db, venue_id='a')
        seed_synthetic(self.db, venue_id='b')
        self.db.execute("UPDATE menu_items SET price_cents=888 WHERE venue_id='b' AND item_id='demo-food-1'")
        self.identity = {'venue_id': 'a', 'permissions': {'menu:read'}}
        self.app = make_menu_app(self.db, lambda env: self.identity)
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
    def call(self, path='/api/v1/menu-items', query='', method='GET', headers=None):
        env = {}
        setup_testing_defaults(env)
        env.update(PATH_INFO=path, QUERY_STRING=query, REQUEST_METHOD=method)
        env.update(headers or {})
        recorded = {}
        def start(status, hs): recorded.update(status=status, headers=dict(hs))
        payload = b''.join(self.app(env, start))
        return recorded['status'], json.loads(payload), recorded['headers']
    def test_authenticated_list(self):
        status, body, headers = self.call()
        self.assertEqual(status, '200 OK')
        self.assertEqual(len(body['items']), 2)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
    def test_unauthenticated(self):
        self.identity = None
        self.assertEqual(self.call()[0], '401 Unauthorized')
    def test_no_read_grant(self):
        self.identity['permissions'] = {'menu:write'}
        self.assertEqual(self.call()[0], '403 Forbidden')
    def test_invalid_venue(self):
        self.identity['venue_id'] = ''
        self.assertEqual(self.call()[0], '403 Forbidden')
    def test_no_tenant_leak_even_with_spoofed_headers(self):
        status, body, _ = self.call(headers={'HTTP_X_VENUE_ID': 'b', 'HTTP_X_ROLE': 'admin'})
        self.assertEqual(status, '200 OK')
        self.assertEqual(next(i for i in body['items'] if i['kind'] == 'food')['price_cents'], 650)
    def test_query_venue_rejected(self):
        self.assertEqual(self.call(query='venue_id=b')[0], '400 Bad Request')
    def test_filter_drinks(self):
        self.assertEqual([i['kind'] for i in self.call(query='kind=drink')[1]['items']], ['drink'])
    def test_invalid_and_duplicate_filter(self):
        for q in ['kind=other', 'kind=food&kind=drink', 'kind=', 'bad', 'kind=food&venue=b']:
            self.assertEqual(self.call(query=q)[0], '400 Bad Request')
    def test_non_get_fails_closed(self):
        status, _, headers = self.call(method='POST')
        self.assertEqual(status, '405 Method Not Allowed')
        self.assertEqual(headers['Allow'], 'GET')
    def test_unknown_path(self):
        self.assertEqual(self.call(path='/api/v1/tables')[0], '404 Not Found')
    def test_requires_resolver(self):
        with self.assertRaises(TypeError): make_menu_app(self.db, None)

if __name__ == '__main__': unittest.main()
