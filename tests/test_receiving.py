import unittest
from horeca.purchasing import Requisition, Status
from horeca.receiving import reconcile_delivery


class ReceivingTests(unittest.TestCase):
    def setUp(self):
        self.req = Requisition('r1', 'venue-a', 'worker-1', 'fictional-supplier',
                               'SKU-1', 10, 125, Status.APPROVED, 'manager-1')

    def test_exact_delivery(self):
        result = reconcile_delivery(self.req, venue_id='venue-a', actor_role='receiver', delivered_units=10)
        self.assertEqual((result.accepted_units, result.accepted_value_cents, result.discrepancy), (10, 1250, False))

    def test_shortfall_rejection_and_excess(self):
        short = reconcile_delivery(self.req, venue_id='venue-a', actor_role='manager', delivered_units=9, rejected_units=2)
        self.assertEqual((short.accepted_units, short.missing_units, short.rejected_units, short.discrepancy), (7, 3, 2, True))
        excess = reconcile_delivery(self.req, venue_id='venue-a', actor_role='owner', delivered_units=12)
        self.assertEqual((excess.excess_units, excess.missing_units), (2, 0))

    def test_venue_role_and_approval_gates(self):
        for kwargs, error in [({'venue_id': 'venue-b', 'actor_role': 'receiver'}, PermissionError),
                              ({'venue_id': 'venue-a', 'actor_role': 'staff'}, PermissionError)]:
            with self.assertRaises(error):
                reconcile_delivery(self.req, delivered_units=10, **kwargs)
        draft = Requisition('r2', 'venue-a', 'worker-1', 'fictional-supplier', 'SKU-1', 10, 125)
        with self.assertRaises(ValueError):
            reconcile_delivery(draft, venue_id='venue-a', actor_role='receiver', delivered_units=10)

    def test_invalid_quantities(self):
        for delivered, rejected in [(-1, 0), (1, 2), (True, 0), (1, False), (1.5, 0)]:
            with self.assertRaises(ValueError):
                reconcile_delivery(self.req, venue_id='venue-a', actor_role='receiver',
                                   delivered_units=delivered, rejected_units=rejected)


if __name__ == '__main__':
    unittest.main()
