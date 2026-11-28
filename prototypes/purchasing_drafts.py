"""Offline purchasing prototype; synthetic data only. Run: python -m unittest prototypes.purchasing_drafts"""
import sqlite3
import unittest

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS requisitions (
 venue TEXT NOT NULL, id TEXT NOT NULL, requester TEXT NOT NULL, supplier TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
 approver TEXT, PRIMARY KEY(venue,id));
CREATE TABLE IF NOT EXISTS lines (
 venue TEXT NOT NULL, requisition TEXT NOT NULL, number INTEGER NOT NULL,
 sku TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0),
 unit_cents INTEGER NOT NULL CHECK(unit_cents>=0),
 PRIMARY KEY(venue,requisition,number),
 FOREIGN KEY(venue,requisition) REFERENCES requisitions(venue,id));
CREATE TABLE IF NOT EXISTS drafts (
 venue TEXT NOT NULL, id TEXT NOT NULL, requisition TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'draft' CHECK(status='draft'),
 PRIMARY KEY(venue,id), UNIQUE(venue,requisition),
 FOREIGN KEY(venue,requisition) REFERENCES requisitions(venue,id));
"""

class PurchasingError(ValueError):
    pass

class Purchasing:
    def __init__(self, db):
        self.db = db
        self.db.executescript(SCHEMA)

    def request(self, venue, ident, requester, supplier, lines):
        if not all((venue, ident, requester, supplier)) or not lines:
            raise PurchasingError("required fields and lines")
        if any(not sku or type(qty) is not int or qty <= 0 or type(cents) is not int or cents < 0
               for sku, qty, cents in lines):
            raise PurchasingError("invalid line")
        with self.db:
            self.db.execute("INSERT INTO requisitions(venue,id,requester,supplier) VALUES(?,?,?,?)",
                            (venue,ident,requester,supplier))
            self.db.executemany("INSERT INTO lines VALUES(?,?,?,?,?,?)",
                                [(venue,ident,n,sku,qty,cents)
                                 for n,(sku,qty,cents) in enumerate(lines,1)])

    def decide(self, venue, ident, manager, approved):
        if not venue or not manager:
            raise PurchasingError("manager required")
        with self.db:
            row = self.db.execute(
                "SELECT requester FROM requisitions WHERE venue=? AND id=? AND status='pending'",
                (venue,ident)).fetchone()
            if row is None or row[0] == manager:
                raise PurchasingError("not pending or self approval")
            self.db.execute("UPDATE requisitions SET status=?,approver=? WHERE venue=? AND id=?",
                            ("approved" if approved else "rejected",manager,venue,ident))

    def draft(self, venue, requisition, ident):
        if not all((venue,requisition,ident)):
            raise PurchasingError("required identifiers")
        with self.db:
            row = self.db.execute("SELECT status FROM requisitions WHERE venue=? AND id=?",
                                  (venue,requisition)).fetchone()
            if row != ("approved",):
                raise PurchasingError("approval required")
            self.db.execute("INSERT INTO drafts(venue,id,requisition) VALUES(?,?,?)",
                            (venue,ident,requisition))

    def total_cents(self, venue, ident):
        return self.db.execute(
            "SELECT SUM(quantity*unit_cents) FROM lines WHERE venue=? AND requisition=?",
            (venue,ident)).fetchone()[0]

class PurchasingTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.p = Purchasing(self.db)
        self.p.request("a","r","fictional-requester","fictional-supplier",
                       [("A",2,125),("B",1,90)])

    def tearDown(self):
        self.db.close()

    def test_approved_draft(self):
        self.assertEqual(self.p.total_cents("a","r"),340)
        self.p.decide("a","r","fictional-manager",True)
        self.p.draft("a","r","po")
        self.assertEqual(self.db.execute("SELECT status FROM drafts").fetchone(),("draft",))

    def test_tenant_isolation(self):
        self.assertIsNone(self.p.total_cents("b","r"))
        with self.assertRaises(PurchasingError):
            self.p.decide("b","r","manager",True)

    def test_self_approval_and_rejection(self):
        with self.assertRaises(PurchasingError):
            self.p.decide("a","r","fictional-requester",True)
        self.p.decide("a","r","manager",False)
        with self.assertRaises(PurchasingError):
            self.p.draft("a","r","po")

    def test_invalid_line(self):
        with self.assertRaises(PurchasingError):
            self.p.request("a","bad","person","supplier",[("sku",-1,5)])

    def test_duplicate_draft(self):
        self.p.decide("a","r","manager",True)
        self.p.draft("a","r","po")
        with self.assertRaises(sqlite3.IntegrityError):
            self.p.draft("a","r","po2")

if __name__ == "__main__":
    unittest.main()
