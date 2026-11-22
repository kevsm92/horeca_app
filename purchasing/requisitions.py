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



def submit_draft(
    connection: sqlite3.Connection, *, venue_id: str,
    requisition_id: str, requester_id: str, expected_revision: int,
) -> int:
    """Submit only an owned draft at its expected revision.

    This is an offline domain operation, not an HTTP authorization boundary.
    All identity values MUST come from a verified server-side authorization
    context. A failed compare-and-swap never changes the requisition.
    Returns the new revision.
    """
    if not all(isinstance(v, str) and v.strip()
               for v in (venue_id, requisition_id, requester_id)):
        raise ValueError("venue, requisition and requester are required")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be a positive integer")
    with connection:
        result = connection.execute(
            """UPDATE purchase_requisitions
               SET status = 'submitted', revision = revision + 1
               WHERE id = ? AND venue_id = ? AND requester_id = ?
                 AND status = 'draft' AND revision = ?""",
            (requisition_id, venue_id, requester_id, expected_revision),
        )
        if result.rowcount != 1:
            raise ValueError("draft not found, not owned, or revision conflict")
    return expected_revision + 1


def approve_submitted(
    connection: sqlite3.Connection, *, venue_id: str,
    requisition_id: str, approver_id: str, expected_revision: int,
) -> int:
    """Approve a submitted requisition with requester/approver separation.

    Offline domain operation only. The caller MUST verify that approver_id
    has approval authority for this venue using server-side RBAC. This
    function enforces only venue ownership, separation of duties and CAS.
    """
    if not all(isinstance(v, str) and v.strip()
               for v in (venue_id, requisition_id, approver_id)):
        raise ValueError("venue, requisition and approver are required")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be a positive integer")
    with connection:
        result = connection.execute(
            """UPDATE purchase_requisitions
               SET status = 'approved', revision = revision + 1
               WHERE id = ? AND venue_id = ? AND status = 'submitted'
                 AND requester_id <> ? AND revision = ?""",
            (requisition_id, venue_id, approver_id, expected_revision),
        )
        if result.rowcount != 1:
            raise ValueError("not submitted, same requester, wrong venue or revision conflict")
    return expected_revision + 1


def reject_submitted(
    connection: sqlite3.Connection, *, venue_id: str,
    requisition_id: str, reviewer_id: str, expected_revision: int,
) -> int:
    """Reject a submitted offline requisition without deleting its history.

    The authenticated caller MUST independently verify reviewer approval
    authority for this venue. Requesters cannot reject their own submissions.
    This is not an HTTP authorization boundary. Returns the new revision.
    """
    if not all(isinstance(v, str) and v.strip()
               for v in (venue_id, requisition_id, reviewer_id)):
        raise ValueError("venue, requisition and reviewer are required")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be a positive integer")
    with connection:
        result = connection.execute(
            """UPDATE purchase_requisitions
               SET status = 'rejected', revision = revision + 1
               WHERE id = ? AND venue_id = ? AND status = 'submitted'
                 AND requester_id <> ? AND revision = ?""",
            (requisition_id, venue_id, reviewer_id, expected_revision),
        )
        if result.rowcount != 1:
            raise ValueError("not submitted, same requester, wrong venue or revision conflict")
    return expected_revision + 1


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


        def test_submit_draft_enforces_owner_venue_and_revision(self):
            rid = create_draft(
                self.db, venue_id="venue-a", requester_id="fictional-requester",
                supplier_id="fictional-supplier", lines=[("FLOUR", 1, 150)],
            )
            for changes in (
                {"venue_id": "venue-b"},
                {"requester_id": "another-requester"},
                {"expected_revision": 2},
            ):
                args = dict(venue_id="venue-a", requisition_id=rid,
                            requester_id="fictional-requester",
                            expected_revision=1)
                args.update(changes)
                with self.assertRaises(ValueError):
                    submit_draft(self.db, **args)
            self.assertEqual(submit_draft(
                self.db, venue_id="venue-a", requisition_id=rid,
                requester_id="fictional-requester", expected_revision=1), 2)
            with self.assertRaises(ValueError):
                submit_draft(self.db, venue_id="venue-a", requisition_id=rid,
                             requester_id="fictional-requester",
                             expected_revision=1)
            self.assertEqual(self.db.execute(
                "SELECT status, revision FROM purchase_requisitions WHERE id=?",
                (rid,)).fetchone(), ("submitted", 2))
            self.assertEqual(list_drafts(self.db, venue_id="venue-a"), [])

        def test_approval_requires_distinct_approver_and_matching_revision(self):
            rid = create_draft(
                self.db, venue_id="venue-a", requester_id="fictional-requester",
                supplier_id="fictional-supplier", lines=[("FLOUR", 1, 150)],
            )
            submit_draft(self.db, venue_id="venue-a", requisition_id=rid,
                         requester_id="fictional-requester", expected_revision=1)
            for changes in (
                {"venue_id": "venue-b"},
                {"approver_id": "fictional-requester"},
                {"expected_revision": 1},
            ):
                args = dict(venue_id="venue-a", requisition_id=rid,
                            approver_id="fictional-manager", expected_revision=2)
                args.update(changes)
                with self.assertRaises(ValueError):
                    approve_submitted(self.db, **args)
            self.assertEqual(
                approve_submitted(self.db, venue_id="venue-a", requisition_id=rid,
                                  approver_id="fictional-manager", expected_revision=2), 3)
            with self.assertRaises(ValueError):
                approve_submitted(self.db, venue_id="venue-a", requisition_id=rid,
                                  approver_id="fictional-manager", expected_revision=2)
            self.assertEqual(self.db.execute(
                "SELECT status, revision FROM purchase_requisitions WHERE id=?",
                (rid,)).fetchone(), ("approved", 3))

        def test_rejection_is_venue_scoped_and_revision_guarded(self):
            rid = create_draft(
                self.db, venue_id="venue-a", requester_id="fictional-requester",
                supplier_id="fictional-supplier", lines=[("MILK", 2, 100)],
            )
            submit_draft(self.db, venue_id="venue-a", requisition_id=rid,
                         requester_id="fictional-requester", expected_revision=1)
            for changes in (
                {"venue_id": "venue-b"},
                {"reviewer_id": "fictional-requester"},
                {"expected_revision": 1},
            ):
                args = dict(venue_id="venue-a", requisition_id=rid,
                            reviewer_id="fictional-manager", expected_revision=2)
                args.update(changes)
                with self.assertRaises(ValueError):
                    reject_submitted(self.db, **args)
            self.assertEqual(reject_submitted(
                self.db, venue_id="venue-a", requisition_id=rid,
                reviewer_id="fictional-manager", expected_revision=2), 3)
            with self.assertRaises(ValueError):
                reject_submitted(self.db, venue_id="venue-a", requisition_id=rid,
                                 reviewer_id="fictional-manager", expected_revision=3)
            with self.assertRaises(ValueError):
                approve_submitted(self.db, venue_id="venue-a", requisition_id=rid,
                                  approver_id="fictional-manager", expected_revision=3)
            self.assertEqual(self.db.execute(
                "SELECT status, revision FROM purchase_requisitions WHERE id=?",
                (rid,)).fetchone(), ("rejected", 3))

    unittest.main()
