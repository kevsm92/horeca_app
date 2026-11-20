"""Offline-only WSGI menu read adapter. No listener or authentication provider.

resolve_session must authenticate independently of client venue headers/queries.
Never expose publicly until session, CSRF/origin and deployment gates are verified.
"""
import json
import sqlite3
from menu_catalog_store import list_items


def make_app(resolve_session, connect):
    """Inject trusted session resolver and venue catalog SQLite connection factory."""
    def app(environ, start_response):
        def reply(status, payload):
            body = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            start_response(status, [('Content-Type', 'application/json; charset=utf-8'),
                                    ('Content-Length', str(len(body))),
                                    ('Cache-Control', 'no-store'),
                                    ('X-Content-Type-Options', 'nosniff')])
            return [body]

        if environ.get('PATH_INFO') != '/api/v1/menu-items':
            return reply('404 Not Found', {'error': 'not_found'})
        if environ.get('REQUEST_METHOD') != 'GET':
            return reply('405 Method Not Allowed', {'error': 'method_not_allowed'})
        try:
            session = resolve_session(environ)
        except Exception:
            return reply('401 Unauthorized', {'error': 'unauthorized'})
        if not isinstance(session, dict) or not isinstance(session.get('venue_id'), str) or not session['venue_id'].strip():
            return reply('401 Unauthorized', {'error': 'unauthorized'})
        permissions = session.get('permissions')
        if not isinstance(permissions, (tuple, list, frozenset, set)) or 'menu:read' not in permissions:
            return reply('403 Forbidden', {'error': 'forbidden'})
        try:
            db = connect()
            try:
                items = list_items(db, venue_id=session['venue_id'])
            finally:
                db.close()
        except (sqlite3.Error, ValueError, OSError):
            return reply('503 Service Unavailable', {'error': 'catalog_unavailable'})
        return reply('200 OK', {'items': items})
    return app


if __name__ == '__main__':
    import unittest
    from menu_catalog_store import initialize, upsert_item

    class ContractTests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(':memory:')
            initialize(self.db)
            for venue, price in [('venue-a', 300), ('venue-b', 900)]:
                upsert_item(self.db, venue_id=venue, item_id='tea', category='drink',
                            name='Synthetic Tea', price_cents=price, available=True)
            self.db.commit()
            self.dump = '\n'.join(self.db.iterdump())

        def call(self, session, path='/api/v1/menu-items', method='GET', broken=False):
            def connect():
                if broken:
                    raise sqlite3.OperationalError('synthetic failure')
                db = sqlite3.connect(':memory:')
                db.executescript(self.dump)
                return db
            app = make_app(lambda env: session, connect)
            statuses = []
            response = app({'PATH_INFO': path, 'REQUEST_METHOD': method,
                            'QUERY_STRING': 'venue_id=venue-b',
                            'HTTP_X_VENUE_ID': 'venue-b'},
                           lambda status, headers: statuses.append((status, dict(headers))))
            return statuses[0], json.loads(b''.join(response))

        def test_venue_from_session_only(self):
            status, payload = self.call({'venue_id': 'venue-a', 'permissions': ['menu:read']})
            self.assertEqual(status[0], '200 OK')
            self.assertEqual(payload['items'][0]['price_cents'], 300)
            self.assertEqual(status[1]['Cache-Control'], 'no-store')

        def test_missing_auth(self):
            self.assertEqual(self.call(None)[0][0], '401 Unauthorized')

        def test_missing_permission(self):
            self.assertEqual(self.call({'venue_id': 'venue-a', 'permissions': []})[0][0], '403 Forbidden')

        def test_missing_venue(self):
            self.assertEqual(self.call({'permissions': ['menu:read']})[0][0], '401 Unauthorized')

        def test_fail_closed_storage(self):
            self.assertEqual(self.call({'venue_id': 'venue-a', 'permissions': ['menu:read']}, broken=True)[0][0], '503 Service Unavailable')

        def test_no_write_methods(self):
            self.assertEqual(self.call(None, method='POST')[0][0], '405 Method Not Allowed')

        def test_unknown_path(self):
            self.assertEqual(self.call(None, path='/api/v1/tables')[0][0], '404 Not Found')

    unittest.main()
