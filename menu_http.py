"""Private read-only WSGI menu endpoint; host supplies trusted session resolver.

Not a standalone server. Never expose publicly without complete security review.
"""
import json
import sqlite3
from menu_catalog import list_items


def make_app(connect_db, resolve_session):
    """resolve_session(environ) returns trusted {venue_id, permissions} or None.

    Host must implement authentication, session revocation, origin/CSRF policy
    and secure cookie handling. Never derive venue from request headers.
    """
    def app(environ, start_response):
        def respond(status, payload):
            body = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            start_response(status, [('Content-Type', 'application/json; charset=utf-8'),
                                    ('Content-Length', str(len(body))),
                                    ('Cache-Control', 'no-store'),
                                    ('X-Content-Type-Options', 'nosniff')])
            return [body]

        if environ.get('PATH_INFO') != '/api/v1/menu-items':
            return respond('404 Not Found', {'error': 'not_found'})
        if environ.get('REQUEST_METHOD') != 'GET':
            return respond('405 Method Not Allowed', {'error': 'method_not_allowed'})
        try:
            principal = resolve_session(environ)
        except Exception:
            return respond('503 Service Unavailable', {'error': 'session_unavailable'})
        if not isinstance(principal, dict):
            return respond('401 Unauthorized', {'error': 'unauthorized'})
        venue = principal.get('venue_id')
        permissions = principal.get('permissions')
        if not isinstance(venue, str) or not venue.strip() or not isinstance(permissions, (set, frozenset, list, tuple)) or 'menu:read' not in permissions:
            return respond('403 Forbidden', {'error': 'forbidden'})
        try:
            with connect_db() as db:
                items = list_items(db, venue)
        except (sqlite3.Error, ValueError):
            return respond('503 Service Unavailable', {'error': 'catalog_unavailable'})
        return respond('200 OK', {'items': items})
    return app
