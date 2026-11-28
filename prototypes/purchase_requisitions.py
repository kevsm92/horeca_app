"""Offline venue-scoped purchase requisition domain; synthetic data only."""
import sqlite3

def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS purchase_requisitions (
      venue_id TEXT NOT NULL, requisition_id TEXT NOT NULL,
      supplier_id TEXT NOT NULL, item_name TEXT NOT NULL,
      quantity INTEGER NOT NULL CHECK(quantity > 0),
      unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0),
      status TEXT NOT NULL CHECK(status IN ('draft','submitted','approved','rejected')),
      requested_by TEXT NOT NULL, reviewed_by TEXT,
      PRIMARY KEY(venue_id,requisition_id))""")

def create_draft(db, *, venue_id, requisition_id, supplier_id, item_name,
                 quantity, unit_price_cents, requested_by):
    if not all(isinstance(x,str) and x.strip() for x in
               (venue_id,requisition_id,supplier_id,item_name,requested_by)):
        raise ValueError("nonempty identifiers and item name required")
    if type(quantity) is not int or quantity <= 0 or type(unit_price_cents) is not int or unit_price_cents < 0:
        raise ValueError("invalid integer quantity or cents")
    with db:
        db.execute("""INSERT INTO purchase_requisitions VALUES
          (?,?,?,?,?,?,'draft',?,NULL)""",
          (venue_id,requisition_id,supplier_id,item_name,quantity,unit_price_cents,requested_by))

def transition(db, *, venue_id, requisition_id, actor_id, actor_role, action):
    """False for foreign/missing requisitions or invalid transitions; never sends orders."""
    if action not in ('submit','approve','reject') or not venue_id or not actor_id:
        return False
    with db:
        row=db.execute("""SELECT status,requested_by FROM purchase_requisitions
          WHERE venue_id=? AND requisition_id=?""",(venue_id,requisition_id)).fetchone()
        if row is None:
            return False
        status,requester=row
        if action=='submit':
            if status!='draft' or actor_id!=requester:
                return False
            next_status,reviewer='submitted',None
        else:
            if status!='submitted' or actor_role!='manager' or actor_id==requester:
                return False
            next_status,reviewer=('approved' if action=='approve' else 'rejected'),actor_id
        result=db.execute("""UPDATE purchase_requisitions SET status=?,reviewed_by=?
          WHERE venue_id=? AND requisition_id=? AND status=?""",
          (next_status,reviewer,venue_id,requisition_id,status))
        return result.rowcount==1
