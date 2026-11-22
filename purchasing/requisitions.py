"""Offline, synthetic purchase requisition store. No network or order submission."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from uuid import uuid4


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS purchase_requisitions (
    id TEXT PRIMARY KEY,
    venue_id TEXT NOT NULL,
    requester_id TEXT NOT NULL,
    supplier_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK(status IN ('draft', 'submitted', 'approved', 'rejected')),
    revision INTEGER NOT NULL DEFAULT 1 CHECK(revision > 0),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS purchase_requisition_lines (
    id TEXT PRIMARY KEY,
    requisition_id TEXT NOT NULL REFERENCES purchase_requisitions(id),
    venue_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0),
    CHECK(length(sku) > 0)
);
CREATE INDEX IF NOT EXISTS idx_requisition_venue
    ON purchase_requisitions(venue_id, status);
"""


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)


def create_draft(
    connection: sqlite3.Connection, *,
    venue_id: str, requester_id: str, supplier_id: str,
    lines: list[tuple[str, int, int]],
) -> str:
    """Create one venue-scoped offline requisition, atomically.

    Caller MUST derive venue_id and requester_id from an authenticated server
    session; this domain function is not an HTTP authorization boundary.
    """
    if not all(isinstance(x, str) and x.strip()
               for x in (venue_id, requester_id, supplier_id)):
        raise ValueError("venue, requester and supplier are required")
    if not lines:
        raise ValueError("at least one line is required")
    total = 0
    for sku, quantity, price in lines:
        if (not isinstance(sku, str) or not sku.strip()
                or type(quantity) is not int or quantity <= 0
                or type(price) is not int or price < 0):
            raise ValueError("invalid SKU, quantity or price")
        total += quantity * price
        if total > 9_223_372_036_854_775_807:
            raise ValueError("total exceeds signed 64-bit cents")
    requisition_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    with connection:
        connection.execute(
            """INSERT INTO purchase_requisitions
               (id, venue_id, requester_id, supplier_id, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (requisition_id, venue_id, requester_id, supplier_id, timestamp),
        )
        connection.executemany(
            """INSERT INTO purchase_requisition_lines
               (id, requisition_id, venue_id, sku, quantity, unit_price_cents)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [(str(uuid4()), requisition_id, venue_id, sku, qty, price)
             for sku, qty, price in lines],
        )
    return requisition_id


def list_drafts(connection: sqlite3.Connection, *, venue_id: str) -> list[tuple]:
    """Read only this venue's draft requisitions; no cross-tenant lookup."""
    if not venue_id:
        raise ValueError("venue is required")
    return connection.execute(
        """SELECT r.id, r.supplier_id, r.revision,
                  SUM(l.quantity * l.unit_price_cents) AS total_cents
           FROM purchase_requisitions r
           JOIN purchase_requisition_lines l
             ON l.requisition_id = r.id AND l.venue_id = r.venue_id
           WHERE r.venue_id = ? AND r.status = 'draft'
           GROUP BY r.id, r.supplier_id, r.revision
           ORDER BY r.created_at, r.id""",
        (venue_id,),
    ).fetchall()


if __name__ == "__main__":
    import unittest

    class RequisitionTests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(":memory:")
            initialize(self.db)

        def tearDown(self):
            self.db.close()

        def test_draft_totals_and_tenant_isolation(self):
            rid = create_draft(
                self.db, venue_id="venue-a", requester_id="fictional-user",
                supplier_id="fictional-supplier",
                lines=[("FLOUR", 2, 325), ("MILK", 3, 199)],
            )
            self.assertEqual(list_drafts(self.db, venue_id="venue-a"),
                             [(rid, "fictional-supplier", 1, 1247)])
            self.assertEqual(list_drafts(self.db, venue_id="venue-b"), [])

        def test_invalid_input_writes_nothing(self):
            for lines in ([], [("FLOUR", 0, 100)],
                          [("FLOUR", 1, -1)], [("FLOUR", True, 1)],
                          [("FLOUR", 2**63, 2)]):
                with self.assertRaises(ValueError):
                    create_draft(
                        self.db, venue_id="venue-a", requester_id="fictional",
                        supplier_id="fictional", lines=lines,
                    )
            self.assertEqual(list_drafts(self.db, venue_id="venue-a"), [])

        def test_database_failure_rolls_back(self):
            self.db.execute("""CREATE TRIGGER reject_line BEFORE INSERT
                               ON purchase_requisition_lines
                               BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END""")
            with self.assertRaises(sqlite3.IntegrityError):
                create_draft(
                    self.db, venue_id="venue-a", requester_id="fictional",
                    supplier_id="fictional", lines=[("FLOUR", 1, 100)],
                )
            self.assertEqual(
                self.db.execute("SELECT COUNT(*) FROM purchase_requisitions")
                .fetchone()[0], 0,
            )

    unittest.main()
