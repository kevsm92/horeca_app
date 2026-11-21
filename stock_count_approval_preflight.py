"""Offline preflight for a manager-reviewed stock recount; never posts stock.

Inputs must be resolved from authenticated staff and trusted venue ledger state.
"""


def preflight_count_approval(*, venue_id, sku_id, recount, current_revision,
                             manager_id, authorized_manager_ids):
    """Fail closed on stale stock or disputed recount before any adjustment."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if not isinstance(sku_id, str) or not sku_id.strip():
        raise ValueError('SKU required')
    if not isinstance(recount, dict):
        raise ValueError('trusted recount required')
    if recount.get('venue_id') != venue_id:
        raise PermissionError('cross-venue recount denied')
    if recount.get('sku_id') != sku_id:
        raise ValueError('SKU mismatch')
    revision = recount.get('snapshot_revision')
    if type(revision) is not int or revision < 0:
        raise ValueError('invalid recount revision')
    if type(current_revision) is not int or current_revision < 0:
        raise ValueError('invalid current revision')
    if not isinstance(manager_id, str) or not manager_id.strip():
        raise PermissionError('manager identity required')
    if not isinstance(authorized_manager_ids, (set, frozenset)) or manager_id not in authorized_manager_ids:
        raise PermissionError('manager authorization required')
    if recount.get('status') != 'consistent_pending_manager_review':
        raise ValueError('disputed or unknown recount cannot be approved')
    if recount.get('ledger_adjustment_posted') is not False or recount.get('certified') is not False:
        raise ValueError('recount must be unposted and uncertified')
    if current_revision != revision:
        raise ValueError('stale count: ledger revision changed')
    return {'venue_id': venue_id, 'sku_id': sku_id, 'snapshot_revision': revision,
            'status': 'eligible_for_separate_transactional_review',
            'approved': False, 'ledger_adjustment_posted': False, 'certified': False}
