"""Unhosted, read-only WSGI floor-plan endpoint with server-derived venue identity.

No listener, session issuer, test identity or public deployment is included.
The trusted resolver must independently grant 'tables:read'; menu:read is insufficient.
"""
import json
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS floor_physical_tables (
 venue_id TEXT NOT NULL CHECK(length(trim(venue_id))>0),
 table_id TEXT NOT NULL CHECK(length(trim(table_id))>0),
 physical_seats INTEGER NOT NULL CHECK(physical_seats BETWEEN 1 AND 100),
 occupied_guests INTEGER NOT NULL DEFAULT 0 CHECK(occupied_guests>=0 AND occupied_guests<=physical_seats),
 PRIMARY KEY(venue_id,table_id)
);
CREATE TABLE IF NOT EXISTS floor_layout_meta (
 venue_id TEXT PRIMARY KEY CHECK(length(trim(venue_id))>0),
 revision INTEGER NOT NULL DEFAULT 0 CHECK(revision>=0)
);
CREATE TABLE IF NOT EXISTS floor_placements (
 venue_id TEXT NOT NULL,
 table_id TEXT NOT NULL,
 x_percent REAL NOT NULL CHECK(x_percent BETWEEN 10 AND 90),
 y_percent REAL NOT NULL CHECK(y_percent BETWEEN 10 AND 90),
 PRIMARY KEY(venue_id,table_id),
 FOREIGN KEY(venue_id,table_id) REFERENCES floor_physical_tables(venue_id,table_id)
);
"""

def initialize_floor_plan(db):
    db.executescript(SCHEMA)

def read_floor_plan(db, *, authorized_venue_id):
    if not isinstance(authorized_venue_id, str) or not authorized_venue_id.strip():
        raise ValueError('trusted venue required')
    # All queries are parameterized and every read includes the server-owned venue.
    rows = db.execute('SELECT table_id,physical_seats,occupied_guests FROM floor_physical_tables '
                      'WHERE venue_id=? ORDER BY table_id', (authorized_venue_id,)).fetchall()
    placements = db.execute('SELECT table_id,x_percent,y_percent FROM floor_placements '
                            'WHERE venue_id=? ORDER BY table_id', (authorized_venue_id,)).fetchall()
    revision = db.execute('SELECT revision FROM floor_layout_meta WHERE venue_id=?',
                          (authorized_venue_id,)).fetchone()
    return {
        'revision': revision[0] if revision else 0,
        'tables': [{'id': r[0], 'physical_seats': r[1], 'occupied_guests': r[2]} for r in rows],
        'placements': [{'table_id': r[0], 'x_percent': r[1], 'y_percent': r[2]} for r in placements],
    }

def make_floor_plan_app(db, resolve_session):
    if not callable(resolve_session):
        raise TypeError('trusted session resolver required')
    def app(environ, start_response):
        def respond(status, payload, extra=()):
            body = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            start_response(status, [('Content-Type', 'application/json; charset=utf-8'),
                                    ('Content-Length', str(len(body))),
                                    ('Cache-Control', 'no-store'),
                                    ('X-Content-Type-Options', 'nosniff')] + list(extra))
            return [body]
        if environ.get('PATH_INFO') != '/api/v1/floor-plan':
            return respond('404 Not Found', {'error': 'not_found'})
        if environ.get('REQUEST_METHOD') != 'GET':
            return respond('405 Method Not Allowed', {'error': 'method_not_allowed'}, [('Allow', 'GET')])
        if environ.get('QUERY_STRING'):
            return respond('400 Bad Request', {'error': 'invalid_query'})
        try:
            identity = resolve_session(environ)
        except sqlite3.Error:
            return respond('503 Service Unavailable', {'error': 'temporarily_unavailable'})
        if not isinstance(identity, dict):
            return respond('401 Unauthorized', {'error': 'unauthenticated'})
        venue = identity.get('venue_id')
        permissions = identity.get('permissions')
        if not isinstance(venue, str) or not venue.strip() or not isinstance(permissions, (set, frozenset)) or 'tables:read' not in permissions:
            return respond('403 Forbidden', {'error': 'forbidden'})
        try:
            payload = read_floor_plan(db, authorized_venue_id=venue)
        except sqlite3.Error:
            return respond('503 Service Unavailable', {'error': 'temporarily_unavailable'})
        return respond('200 OK', payload)
    return app
