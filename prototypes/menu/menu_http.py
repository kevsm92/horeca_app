"""Unhosted read-only WSGI menu endpoint. Requires trusted server-side session resolver.

No listener, login route, demo identity, or public deployment is provided.
"""
import json
import sqlite3
from urllib.parse import parse_qs
from menu_catalog import list_items

def make_menu_app(db, resolve_session):
    """Resolver(environ) must validate server-side session, expiry and venue grants."""
    if not callable(resolve_session):
        raise TypeError('trusted session resolver required')

    def app(environ, start_response):
        def respond(status, payload, extra=()):
            body = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            start_response(status, [
                ('Content-Type', 'application/json; charset=utf-8'),
                ('Content-Length', str(len(body))),
                ('Cache-Control', 'no-store'),
                ('X-Content-Type-Options', 'nosniff'),
            ] + list(extra))
            return [body]

        if environ.get('PATH_INFO') != '/api/v1/menu-items':
            return respond('404 Not Found', {'error': 'not_found'})
        if environ.get('REQUEST_METHOD') != 'GET':
            return respond('405 Method Not Allowed', {'error': 'method_not_allowed'}, [('Allow', 'GET')])
        try:
            params = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True,
                              strict_parsing=True, max_num_fields=4)
        except ValueError:
            return respond('400 Bad Request', {'error': 'invalid_query'})
        if set(params) - {'kind'} or len(params.get('kind', [])) > 1:
            return respond('400 Bad Request', {'error': 'invalid_query'})
        kind = params.get('kind', [None])[0]
        if kind is not None and kind not in ('food', 'drink'):
            return respond('400 Bad Request', {'error': 'invalid_kind'})
        # Client headers and query parameters are never trusted for identity/venue.
        try:
            identity = resolve_session(environ)
        except sqlite3.Error:
            return respond('503 Service Unavailable', {'error': 'temporarily_unavailable'})
        if not isinstance(identity, dict):
            return respond('401 Unauthorized', {'error': 'unauthenticated'})
        venue = identity.get('venue_id')
        if not isinstance(venue, str) or not venue.strip():
            return respond('403 Forbidden', {'error': 'forbidden'})
        permissions = identity.get('permissions')
        if not isinstance(permissions, (set, frozenset)) or 'menu:read' not in permissions:
            return respond('403 Forbidden', {'error': 'forbidden'})
        try:
            items = list_items(db, authorized_venue_id=venue, kind=kind)
        except sqlite3.Error:
            return respond('503 Service Unavailable', {'error': 'temporarily_unavailable'})
        return respond('200 OK', {'items': items})
    return app
