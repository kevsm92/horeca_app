"""Compose the existing menu WSGI endpoint with database-backed sessions.

Unhosted integration factory: no login route, listener, or production deployment.
The caller owns the SQLite connection and its thread/lifecycle policy.
"""
from menu_http import make_menu_app
from menu_sessions import resolve_menu_session


def make_authenticated_menu_app(db, *, now=None):
    """Build read-only WSGI app with server-derived venue and permission grants.

    `now` is for deterministic tests only; production callers should omit it.
    The session schema must be initialized by the trusted application bootstrap.
    """
    return make_menu_app(db, lambda environ: resolve_menu_session(db, environ, now=now))
