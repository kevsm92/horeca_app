import sqlite3
import unittest
from receiving_invoice_multi_receipt import accepted_po_receipt_lines

class MultiReceiptTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.executescript("""
          CREATE TABLE receiving_purchase_orders(venue_id TEXT,purchase_order_id TEXT);
          CREATE TABLE receiving_receipts(venue_id TEXT,receipt_id TEXT,purchase_order_id TEXT,status TEXT);
          CREATE TABLE receiving_receipt_lines(venue_id TEXT,receipt_id TEXT,sku TEXT,accepted_units INTEGER,agreed_unit_cents INTEGER);
          INSERT INTO receiving_purchase_orders VALUES('fictional-a','po-1');
          INSERT INTO receiving_receipts VALUES('fictional-a','r-1','po-1','accepted');
          INSERT INTO receiving_receipts VALUES('fictional-a','r-2','po-1','accepted');
          INSERT INTO receiving_receipt_lines VALUES('fictional-a','r-1','SYN-1',2,125);
          INSERT INTO receiving_receipt_lines VALUES('fictional-a','r-2','SYN-1',3,125);
        """)
    def tearDown(self): self.db.close()
    def load(self, **kwargs):
        args=dict(venue_id='fictional-a',purchase_order_id='po-1',receipt_ids=('r-1','r-2'))
        args.update(kwargs)
        return accepted_po_receipt_lines(self.db,**args)
    def test_aggregate(self): self.assertEqual((self.load()[0].accepted_units,self.load()[0].agreed_unit_cents),(5,125))
    def test_single_receipt(self): self.assertEqual(self.load(receipt_ids=('r-1',))[0].accepted_units,2)
    def test_duplicate_receipt(self):
        with self.assertRaises(ValueError): self.load(receipt_ids=('r-1','r-1'))
    def test_cross_venue(self):
        with self.assertRaises(ValueError): self.load(venue_id='fictional-b')
    def test_other_po(self):
        self.db.execute("UPDATE receiving_receipts SET purchase_order_id='po-2' WHERE receipt_id='r-2'")
        with self.assertRaises(ValueError): self.load()
    def test_unaccepted(self):
        self.db.execute("UPDATE receiving_receipts SET status='draft' WHERE receipt_id='r-2'")
        with self.assertRaises(ValueError): self.load()
    def test_price_disagreement(self):
        self.db.execute("UPDATE receiving_receipt_lines SET agreed_unit_cents=126 WHERE receipt_id='r-2'")
        with self.assertRaises(ValueError): self.load()
    def test_negative_units(self):
        self.db.execute("UPDATE receiving_receipt_lines SET accepted_units=-1 WHERE receipt_id='r-2'")
        with self.assertRaises(ValueError): self.load()
    def test_missing_receipt(self):
        with self.assertRaises(ValueError): self.load(receipt_ids=('r-1','absent'))
    def test_no_lines(self):
        self.db.execute("DELETE FROM receiving_receipt_lines WHERE receipt_id='r-2'")
        with self.assertRaises(ValueError): self.load()
    def test_empty_selection(self):
        with self.assertRaises(ValueError): self.load(receipt_ids=())

if __name__=='__main__': unittest.main()
