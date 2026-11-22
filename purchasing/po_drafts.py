"""Offline purchase-order draft projection from an approved requisition.

This is a domain function, NOT an authentication or approval endpoint. Caller
must derive venue from an authorized server-side context. No outbound I/O.
"""
import sqlite3
from uuid import uuid4


SCHEMA = """
CREATE TABLE IF NOT EXISTS offline_po_drafts (
    id TEXT PRIMARY KEY,
    venue_id TEXT NOT NULL,
    requisition_id TEXT NOT NULL REFERENCES purchase_requisitions(id),
    approved_revision INTEGER NOT NULL CHECK(approved_revision > 0),
    supplier_id TEXT NOT NULL,
    total_cents INTEGER NOT NULL CHECK(total_cents >= 0),
    offline_only INTEGER NOT NULL DEFAULT 1 CHECK(offline_only = 1),
    UNIQUE(venue_id, requisition_id, approved_revision)
);
"""


def initialize(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(SCHEMA)


def create_offline_draft(connection: sqlite3.Connection, *, venue_id: str,
                         requisition_id: str, expected_revision: int) -> str:
    """Idempotently snapshot an approved requisition; never send an order."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError("venue required")
    if not isinstance(requisition_id, str) or not requisition_id.strip():
        raise ValueError("requisition required")
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValueError("positive revision required")
    # SQLite writes serialize; INSERT OR IGNORE handles concurrent promotions.
    with connection:
        record = connection.execute(
            """SELECT supplier_id FROM purchase_requisitions
               WHERE id=? AND venue_id=? AND status='approved' AND revision=?""",
            (requisition_id, venue_id, expected_revision),
        ).fetchone()
        if record is None:
            raise ValueError("approved requisition not found at revision")
        lines = connection.execute(
            """SELECT quantity, unit_price_cents FROM purchase_requisition_lines
               WHERE requisition_id=? AND venue_id=?""",
            (requisition_id, venue_id),
        ).fetchall()
        if not lines:
            raise ValueError("approved requisition has no lines")
        total = sum(qty * price for qty, price in lines)
        if total > 2**63 - 1:
            raise ValueError("total exceeds signed 64-bit cents")
        connection.execute(
            """INSERT OR IGNORE INTO offline_po_drafts
               (id, venue_id, requisition_id, approved_revision, supplier_id, total_cents)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(uuid4()), venue_id, requisition_id, expected_revision, record[0], total),
        )
        return connection.execute(
            """SELECT id FROM offline_po_drafts
               WHERE venue_id=? AND requisition_id=? AND approved_revision=?""",
            (venue_id, requisition_id, expected_revision),
        ).fetchone()[0]


if __name__ == "__main__":
    import unittest

    class DraftTests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(":memory:")
            self.db.executescript("""
                CREATE TABLE purchase_requisitions (
                    id TEXT PRIMARY KEY, venue_id TEXT, supplier_id TEXT,
                    status TEXT, revision INTEGER);
                CREATE TABLE purchase_requisition_lines (
                    requisition_id TEXT, venue_id TEXT, quantity INTEGER,
                    unit_price_cents INTEGER);
                INSERT INTO purchase_requisitions VALUES
                    ('approved-a','a','fictional-supplier','approved',3),
                    ('submitted-a','a','fictional-supplier','submitted',2);
                INSERT INTO purchase_requisition_lines VALUES
                    ('approved-a','a',2,125),('approved-a','a',3,200);
            """)
            initialize(self.db)

        def tearDown(self):
            self.db.close()

        def test_approved_snapshot_and_idempotency(self):
            first = create_offline_draft(self.db, venue_id="a",
                requisition_id="approved-a", expected_revision=3)
            self.assertEqual(first, create_offline_draft(self.db, venue_id="a",
                requisition_id="approved-a", expected_revision=3))
            self.assertEqual(self.db.execute(
                "SELECT total_cents,offline_only FROM offline_po_drafts"
            ).fetchall(), [(850, 1)])

        def test_wrong_venue_state_or_revision_does_not_write(self):
            for venue, rid, rev in (("b", "approved-a", 3),
                                     ("a", "submitted-a", 2),
                                     ("a", "approved-a", 2)):
                with self.assertRaises(ValueError):
                    create_offline_draft(self.db, venue_id=venue,
                        requisition_id=rid, expected_revision=rev)
            self.assertEqual(self.db.execute(
                "SELECT COUNT(*) FROM offline_po_drafts").fetchone()[0], 0)

        def test_empty_lines_and_overflow_fail_closed(self):
            self.db.execute("DELETE FROM purchase_requisition_lines")
            with self.assertRaises(ValueError):
                create_offline_draft(self.db, venue_id="a",
                    requisition_id="approved-a", expected_revision=3)
            self.db.execute("INSERT INTO purchase_requisition_lines VALUES (?,?,?,?)",
                            ("approved-a", "a", 2**62, 4))
            with self.assertRaises(ValueError):
                create_offline_draft(self.db, venue_id="a",
                    requisition_id="approved-a", expected_revision=3)
            self.assertEqual(self.db.execute(
                "SELECT COUNT(*) FROM offline_po_drafts").fetchone()[0], 0)

    unittest.main()
