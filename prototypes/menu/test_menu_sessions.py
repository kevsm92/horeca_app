import sqlite3
import unittest
from menu_sessions import initialize_sessions, resolve_menu_session, provision_test_session

TOKEN = 'ab' * 32

class MenuSessionTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize_sessions(self.db)
        provision_test_session(self.db, token_hex=TOKEN, venue_id='venue-a', expires_at=2000)
    def tearDown(self): self.db.close()
    def resolve(self, cookie=None, now=1000):
        return resolve_menu_session(self.db, {'HTTP_COOKIE': cookie or ''}, now=now)
    def test_valid_session(self):
        self.assertEqual(self.resolve('horeca_session='+TOKEN), {'venue_id':'venue-a','permissions':{'menu:read'}})
    def test_no_token_storage(self):
        self.assertNotIn(TOKEN, repr(self.db.execute('SELECT * FROM menu_sessions').fetchone()))
    def test_expiry(self):
        self.assertIsNone(self.resolve('horeca_session='+TOKEN, now=2000))
    def test_revocation(self):
        self.db.execute('UPDATE menu_sessions SET revoked_at=999')
        self.assertIsNone(self.resolve('horeca_session='+TOKEN))
    def test_invalid_token(self):
        for cookie in ['', 'horeca_session=abc', 'horeca_session='+'ff'*32, 'horeca_session='+TOKEN.upper(), 'horeca_session='+TOKEN+'x']:
            self.assertIsNone(self.resolve(cookie))
    def test_client_venue_spoofing_ignored(self):
        self.assertEqual(resolve_menu_session(self.db, {'HTTP_COOKIE':'horeca_session='+TOKEN,'HTTP_X_VENUE_ID':'venue-b'}, now=1000)['venue_id'],'venue-a')
    def test_missing_grant(self):
        self.db.execute('UPDATE menu_sessions SET can_read_menu=0')
        self.assertEqual(self.resolve('horeca_session='+TOKEN)['permissions'],set())
    def test_oversized_cookie(self):
        self.assertIsNone(self.resolve('x'*4097))
    def test_bad_fixture_token(self):
        with self.assertRaises(ValueError): provision_test_session(self.db,token_hex='bad',venue_id='x',expires_at=2000)

if __name__=='__main__': unittest.main()
