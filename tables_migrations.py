"""Explicit, non-destructive schema version bootstrap for HORECA table prototypes."""
import sqlite3

from tables_foundation import SCHEMA

CURRENT_VERSION = 1


def migrate(db: sqlite3.Connection) -> int:
    """Upgrade a new or unversioned table database to v1 without deleting records.

    Caller must use a connection with isolation_level=None (autocommit), as returned
    by tables_foundation.connect. BEGIN IMMEDIATE serializes concurrent migrators.
    """
    if db.in_transaction:
        raise ValueError("migration requires no active transaction")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("BEGIN IMMEDIATE")
    try:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version > CURRENT_VERSION:
            raise ValueError(f"database version {version} is newer than supported {CURRENT_VERSION}")
        if version == 0:
            # Schema is already provisioned by connect() for existing installations.
            # For uninitialized databases, use complete_statement to retain triggers.
            pending = ''
            for line in SCHEMA.splitlines(keepends=True):
                pending += line
                if sqlite3.complete_statement(pending):
                    statement = pending.strip()
                    if statement and not statement.upper().startswith('PRAGMA'):
                        db.execute(statement)
                    pending = ''
            if pending.strip():
                raise ValueError("incomplete schema statement")
            db.execute(f"PRAGMA user_version={CURRENT_VERSION}")
        db.execute("COMMIT")
        return CURRENT_VERSION
    except BaseException:
        db.execute("ROLLBACK")
        raise
