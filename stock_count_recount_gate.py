"""Offline independent recount gate for disputed stock counts.

Pure function: no staff authentication, physical attestation, or ledger writes.
Caller supplies trusted, venue-scoped count records.
"""


def reconcile_recount(*, venue_id, sku_id, first, second, tolerance_units=0):
    """Require independent actors, matching snapshot and bounded difference."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if not isinstance(sku_id, str) or not sku_id.strip():
        raise ValueError('SKU required')
    if type(tolerance_units) is not int or tolerance_units < 0:
        raise ValueError('invalid tolerance')
    for record in (first, second):
        if not isinstance(record, dict):
            raise ValueError('trusted count record required')
        if record.get('venue_id') != venue_id:
            raise PermissionError('cross-venue recount denied')
        if record.get('sku_id') != sku_id:
            raise ValueError('SKU mismatch')
        if type(record.get('snapshot_revision')) is not int or record['snapshot_revision'] < 0:
            raise ValueError('invalid snapshot revision')
        if type(record.get('counted_units')) is not int or record['counted_units'] < 0:
            raise ValueError('invalid counted units')
        if not isinstance(record.get('actor_id'), str) or not record['actor_id'].strip():
            raise ValueError('actor required')
    if first['actor_id'] == second['actor_id']:
        raise ValueError('independent recount actor required')
    if first['snapshot_revision'] != second['snapshot_revision']:
        raise ValueError('stale recount: snapshot revision mismatch')
    difference = second['counted_units'] - first['counted_units']
    return {'venue_id': venue_id, 'sku_id': sku_id,
            'snapshot_revision': first['snapshot_revision'],
            'difference_units': difference,
            'status': 'consistent_pending_manager_review' if abs(difference) <= tolerance_units
                      else 'disputed_requires_investigation',
            'ledger_adjustment_posted': False, 'certified': False}
