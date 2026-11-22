"""Offline purchase-order draft amendment; never transmits to a supplier."""
from dataclasses import dataclass, replace
from horeca.purchase_orders import PurchaseOrderDraft

MAX_CENTS = 2**63 - 1

@dataclass(frozen=True)
class RevisedDraft:
    draft: PurchaseOrderDraft
    revision: int = 1

    def __post_init__(self):
        if type(self.revision) is not int or self.revision < 1:
            raise ValueError('positive revision required')


def amend_draft(current: RevisedDraft, *, venue_id: str, actor_id: str,
                role: str, expected_revision: int, quantity: int,
                unit_price_cents: int) -> RevisedDraft:
    """Optimistic revision guard; caller must atomically compare-and-swap persistence."""
    draft = current.draft
    if not venue_id or venue_id != draft.venue_id:
        raise PermissionError('wrong venue')
    if role not in ('manager', 'owner') or not actor_id:
        raise PermissionError('manager authorization required')
    if draft.status != 'draft':
        raise ValueError('only offline drafts can be amended')
    if type(expected_revision) is not int or expected_revision != current.revision:
        raise ValueError('stale revision')
    if type(quantity) is not int or quantity <= 0:
        raise ValueError('positive integer quantity required')
    if type(unit_price_cents) is not int or unit_price_cents < 0:
        raise ValueError('nonnegative integer cents required')
    if quantity * unit_price_cents > MAX_CENTS:
        raise ValueError('amount exceeds supported range')
    if (quantity, unit_price_cents) == (draft.quantity, draft.unit_price_cents):
        raise ValueError('no changes')
    return RevisedDraft(replace(draft, quantity=quantity,
                                unit_price_cents=unit_price_cents),
                        current.revision + 1)
