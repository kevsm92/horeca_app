"""Negative WSGI tests for the existing synthetic menu session boundary.

Run: cd prototypes/menu && python -m unittest test_menu_http_security_regressions
No listener, real credentials, or external network.
"""
import json
import tempfile
import unittest
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from menu_app import make_authenticated_menu_app
from menu_catalog import connect, seed_synthetic
from menu_sessions import initialize_sessions, provision_test_session


class MenuHttpSecurityRegressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / "fixture.sqlite")
        initialize_sessions(self.db)
        seed_synthetic(self.db, venue_id="venue-a")
        seed_synthetic(self.db, venue_id="venue-b")
        self.token = "ab" * 32
        provision_test_session(self.db, token_hex=self.token,
                               venue_id="venue-a", expires_at=2000)
        self.app = make_authenticated_menu_app(self.db, now=1000)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def request(self, *, cookie=None, query="", method="GET", headers=None):
        environ = {}
        setup_testing_defaults(environ)
        environ.update(PATH_INFO="/api/v1/menu-items",
                       REQUEST_METHOD=method, QUERY_STRING=query)
        if cookie is not None:
            environ["HTTP_COOKIE"] = cookie
        environ.update(headers or {})
        result = {}
        def start_response(status, response_headers):
            result["status"] = status
            result["headers"] = dict(response_headers)
        result["body"] = json.loads(b"".join(self.app(environ, start_response)))
        return result

    def test_duplicate_session_cookie_fails_closed(self):
        result = self.request(cookie=f"horeca_session={self.token}; horeca_session={self.token}")
        self.assertEqual(result["status"], "401 Unauthorized")

    def test_oversized_cookie_fails_closed(self):
        result = self.request(cookie=f"horeca_session={self.token}; padding=" + "x" * 4100)
        self.assertEqual(result["status"], "401 Unauthorized")

    def test_client_venue_headers_cannot_override_session(self):
        result = self.request(cookie=f"horeca_session={self.token}",
                              headers={"HTTP_X_VENUE_ID": "venue-b",
                                       "HTTP_X_ROLE": "admin"})
        self.assertEqual(result["status"], "200 OK")
        self.assertEqual(len(result["body"]["items"]), 2)
        self.assertEqual(result["headers"]["Cache-Control"], "no-store")

    def test_duplicate_kind_query_rejected(self):
        result = self.request(cookie=f"horeca_session={self.token}",
                              query="kind=food&kind=drink")
        self.assertEqual(result["status"], "400 Bad Request")

    def test_client_selected_venue_rejected(self):
        result = self.request(cookie=f"horeca_session={self.token}",
                              query="venue_id=venue-b")
        self.assertEqual(result["status"], "400 Bad Request")

    def test_post_rejected_without_side_effect(self):
        result = self.request(cookie=f"horeca_session={self.token}", method="POST")
        self.assertEqual(result["status"], "405 Method Not Allowed")
        self.assertEqual(result["headers"]["Allow"], "GET")


if __name__ == "__main__":
    unittest.main()
