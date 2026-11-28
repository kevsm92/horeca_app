"""Explicit loopback-only development server for pre-initialized synthetic menu data.

Not a production server or login service. Never publish this listener.
"""
import argparse
from pathlib import Path
import sqlite3
from wsgiref.simple_server import make_server

from menu_app import make_authenticated_menu_app


def open_existing_database(path):
    """Refuse missing/uninitialized databases; never provision identities."""
    file = Path(path)
    if not file.is_absolute() or not file.is_file():
        raise ValueError('absolute path to an existing SQLite database required')
    db = sqlite3.connect(f'file:{file.as_posix()}?mode=rw', uri=True)
    try:
        db.row_factory = sqlite3.Row
        tables = {row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'menu_items', 'menu_sessions'} <= tables:
            raise ValueError('menu and session schemas must already exist')
        return db
    except BaseException:
        db.close()
        raise


def serve_local(path, *, host='127.0.0.1', port=8765):
    """Single-threaded, loopback-only WSGI; no session creation or CORS."""
    if host != '127.0.0.1':
        raise ValueError('only IPv4 loopback 127.0.0.1 is permitted')
    if not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError('invalid port')
    db = open_existing_database(path)
    try:
        with make_server(host, port, make_authenticated_menu_app(db)) as server:
            server.serve_forever()
    finally:
        db.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Local-only synthetic menu API (no login)')
    parser.add_argument('--database', required=True, help='absolute path to initialized SQLite DB')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args(argv)
    serve_local(args.database, port=args.port)


if __name__ == '__main__':
    main()
