"""Regression: duplicate cookies must not select an attacker-controlled session."""
import sqlite3
import unittest
from menu_sessions import initialize_sessions, provision_test_session, resolve_menu_session

TOKEN = 'ab' * 32

class DuplicateCookieTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize_sessions(self.db)
        provision_test_session(self.db, token_hex=TOKEN, venue_id='venue-a', expires_at=2000)

    def tearDown(self):
        self.db.close()

    def resolve(self, cookie):
        return resolve_menu_session(self.db, {'HTTP_COOKIE': cookie}, now=1000)

    def test_valid_cookie_with_unrelated_cookie(self):
        self.assertEqual(self.resolve('theme=light; horeca_session=' + TOKEN)['venue_id'], 'venue-a')

    def test_duplicate_identical_session_cookie_rejected(self):
        self.assertIsNone(self.resolve('horeca_session=' + TOKEN + '; horeca_session=' + TOKEN))

    def test_duplicate_conflicting_session_cookie_rejected_in_both_orders(self):
        bad = 'cd' * 32
        for cookie in ['horeca_session=' + TOKEN + '; horeca_session=' + bad,
                       'horeca_session=' + bad + '; horeca_session=' + TOKEN]:
            with self.subTest(cookie=cookie):
                self.assertIsNone(self.resolve(cookie))

    def test_no_session_cookie_rejected(self):
        self.assertIsNone(self.resolve('theme=light'))

if __name__ == '__main__':
    unittest.main()
