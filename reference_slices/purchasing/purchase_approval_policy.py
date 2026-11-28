"""Offline, synthetic-only purchase-order approval gate (standalone reference slice).

Not integrated into API/storage. Never dispatches orders or contacts suppliers.
"""
from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    REJECT = 'reject'
    PENDING = 'pending_approval'
    APPROVED = 'approved_for_offline_draft'


@dataclass(frozen=True)
class PurchaseDraft:
    venue_id: str
    requester_id: str
    supplier_venue_id: str
    lines_cents: tuple[tuple[int, int], ...]  # (unit price EUR cents, quantity)


def decide(draft: PurchaseDraft, *, actor_id: str, actor_venue_id: str,
           actor_roles: frozenset[str], approval_limit_cents: int) -> Decision:
    """Fail closed; approval is for an offline draft, NEVER supplier dispatch."""
    if (not draft.venue_id or not draft.requester_id or
            draft.venue_id != actor_venue_id or
            draft.supplier_venue_id != draft.venue_id or
            not draft.lines_cents or
            any(type(price) is not int or type(qty) is not int or
                price < 0 or qty <= 0 for price, qty in draft.lines_cents) or
            type(approval_limit_cents) is not int or approval_limit_cents < 0):
        return Decision.REJECT
    if 'purchase_approver' not in actor_roles or actor_id == draft.requester_id:
        return Decision.PENDING
    total = sum(price * qty for price, qty in draft.lines_cents)
    return Decision.APPROVED if total <= approval_limit_cents else Decision.PENDING


if __name__ == '__main__':
    import unittest

    class ApprovalTests(unittest.TestCase):
        def setUp(self):
            self.draft = PurchaseDraft('venue-a', 'requester', 'venue-a', ((120, 2),))
            self.kw = dict(actor_id='manager', actor_venue_id='venue-a',
                           actor_roles=frozenset({'purchase_approver'}), approval_limit_cents=240)

        def test_exact_limit_approved(self):
            self.assertEqual(decide(self.draft, **self.kw), Decision.APPROVED)

        def test_cross_venue_rejected(self):
            self.assertEqual(decide(self.draft, **(self.kw | {'actor_venue_id': 'venue-b'})), Decision.REJECT)

        def test_supplier_venue_mismatch_rejected(self):
            bad = PurchaseDraft('venue-a', 'requester', 'venue-b', ((120, 2),))
            self.assertEqual(decide(bad, **self.kw), Decision.REJECT)

        def test_requester_cannot_self_approve(self):
            self.assertEqual(decide(self.draft, **(self.kw | {'actor_id': 'requester'})), Decision.PENDING)

        def test_missing_role_pending(self):
            self.assertEqual(decide(self.draft, **(self.kw | {'actor_roles': frozenset()})), Decision.PENDING)

        def test_over_limit_pending(self):
            self.assertEqual(decide(self.draft, **(self.kw | {'approval_limit_cents': 239})), Decision.PENDING)

        def test_invalid_money_rejected(self):
            for lines in (((-1, 1),), ((True, 1),), ((1, 0),), ()):
                with self.subTest(lines=lines):
                    bad = PurchaseDraft('venue-a', 'requester', 'venue-a', lines)
                    self.assertEqual(decide(bad, **self.kw), Decision.REJECT)

    unittest.main()
