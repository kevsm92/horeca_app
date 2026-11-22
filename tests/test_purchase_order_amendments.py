import unittest
from dataclasses import replace
from horeca.purchase_order_amendments import RevisedDraft, amend_draft
from horeca.purchase_orders import PurchaseOrderDraft


class DraftAmendmentTests(unittest.TestCase):
    def setUp(self):
        self.initial = RevisedDraft(PurchaseOrderDraft(
            'po-1', 'venue-a', 'req-1', 'fictional-supplier', 'SKU', 2, 100, 'manager-1'))
        self.args = dict(venue_id='venue-a', actor_id='manager-2', role='manager',
                         expected_revision=1, quantity=3, unit_price_cents=150)

    def test_revision_and_integer_cents(self):
        revised = amend_draft(self.initial, **self.args)
        self.assertEqual((revised.revision, revised.draft.total_cents), (2, 450))
        self.assertEqual(self.initial.draft.total_cents, 200)
        with self.assertRaisesRegex(ValueError, 'stale'):
            amend_draft(revised, **self.args)

    def test_tenant_and_role_denied(self):
        for override in [dict(venue_id='venue-b'), dict(role='staff'), dict(actor_id='')]:
            with self.assertRaises(PermissionError):
                amend_draft(self.initial, **(self.args | override))

    def test_money_and_revision_validation(self):
        for override in [dict(quantity=0), dict(quantity=True),
                         dict(unit_price_cents=-1), dict(unit_price_cents=True),
                         dict(quantity=2**63), dict(expected_revision=True)]:
            with self.assertRaises(ValueError):
                amend_draft(self.initial, **(self.args | override))

    def test_non_draft_and_noop_denied(self):
        with self.assertRaises(ValueError):
            amend_draft(RevisedDraft(replace(self.initial.draft, status='sent')), **self.args)
        with self.assertRaises(ValueError):
            amend_draft(self.initial, **(self.args | dict(quantity=2, unit_price_cents=100)))


if __name__ == '__main__':
    unittest.main()
