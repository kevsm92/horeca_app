import sqlite3
import unittest
from receiving_invoice_batch import InvoiceLine
from receiving_invoice_store import reconcile_stored_receipt


class StoredReceiptTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript('''
            CREATE TABLE receiving_purchase_orders (venue_id TEXT, purchase_order_id TEXT,
                PRIMARY KEY(venue_id,purchase_order_id));
            CREATE TABLE receiving_receipts (venue_id TEXT, receipt_id TEXT, purchase_order_id TEXT,
                status TEXT, PRIMARY KEY(venue_id,receipt_id));
            CREATE TABLE receiving_receipt_lines (venue_id TEXT, receipt_id TEXT, sku TEXT,
                accepted_units INTEGER, agreed_unit_cents INTEGER,
                PRIMARY KEY(venue_id,receipt_id,sku));
        ''')
        self.db.execute('INSERT INTO receiving_purchase_orders VALUES (?,?)', ('fictional-a','po-1'))
        self.db.execute('INSERT INTO receiving_receipts VALUES (?,?,?,?)', ('fictional-a','r-1','po-1','accepted'))
        self.db.execute('INSERT INTO receiving_receipt_lines VALUES (?,?,?,?,?)', ('fictional-a','r-1','SYN-1',4,125))

    def tearDown(self):
        self.db.close()

    def match(self, **kw):
        args=dict(venue_id='fictional-a', purchase_order_id='po-1', receipt_id='r-1',
                  invoice_venue_id='fictional-a', invoice_lines=[InvoiceLine('SYN-1',4,125)])
        args.update(kw)
        return reconcile_stored_receipt(self.db, **args)

    def test_match(self):
        self.assertEqual(self.match().status,'matched')
    def test_variance(self):
        self.assertEqual(self.match(invoice_lines=[InvoiceLine('SYN-1',4,126)]).status,'human_review_required')
    def test_cross_venue_invoice(self):
        with self.assertRaises(PermissionError): self.match(invoice_venue_id='fictional-b')
    def test_cross_venue_receipt_not_found(self):
        with self.assertRaises(ValueError): self.match(venue_id='fictional-b',invoice_venue_id='fictional-b')
    def test_wrong_po(self):
        with self.assertRaises(ValueError): self.match(purchase_order_id='po-other')
    def test_unaccepted_receipt(self):
        self.db.execute("UPDATE receiving_receipts SET status='draft'")
        with self.assertRaises(ValueError): self.match()
    def test_empty_lines(self):
        self.db.execute('DELETE FROM receiving_receipt_lines')
        with self.assertRaises(ValueError): self.match()
    def test_missing_po_record(self):
        self.db.execute('DELETE FROM receiving_purchase_orders')
        with self.assertRaises(ValueError): self.match()
    def test_missing_identity(self):
        with self.assertRaises(ValueError): self.match(receipt_id='')

if __name__=='__main__': unittest.main()
