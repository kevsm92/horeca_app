"""Conservative offline stock availability preview; never alters inventory or orders.

Only batches clearly within their configured deadline count as usable for
replenishment planning. Expiring/unknown batches require human review.
"""
from batch_expiry_preview import preview_batch_expiry


def preview_eligible_stock(*, venue_id, batches, inspected_at):
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue_id required')
    if not isinstance(batches, (list, tuple)):
        raise ValueError('batches must be a sequence')
    seen = set()
    eligible = withheld = 0
    review = []
    for batch in batches:
        if not isinstance(batch, dict) or batch.get('venue_id') != venue_id:
            raise PermissionError('batch venue mismatch')
        batch_id = batch.get('batch_id')
        quantity = batch.get('quantity_units')
        if not isinstance(batch_id, str) or not batch_id.strip() or batch_id in seen:
            raise ValueError('invalid or duplicate batch_id')
        if type(quantity) is not int or quantity < 0:
            raise ValueError('quantity_units must be nonnegative integer')
        seen.add(batch_id)
        result = preview_batch_expiry(inspected_at=inspected_at,
                                      discard_at=batch.get('discard_at'),
                                      original_use_by=batch.get('original_use_by'))
        if result['status'] == 'within_deadline':
            eligible += quantity
        else:
            withheld += quantity
            review.append({'batch_id': batch_id, 'status': result['status'],
                           'quantity_units': quantity})
    return {'venue_id': venue_id, 'eligible_units': eligible,
            'withheld_units': withheld, 'review_batches': review,
            'ledger_modified': False, 'purchase_order_created': False}
