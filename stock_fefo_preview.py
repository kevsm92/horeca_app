"""Offline FEFO picking preview for synthetic inventory batches.

Only batches with verified recorded deadlines are eligible. This module does
not determine food safety, reserve inventory, or mutate any stock ledger.
"""
from datetime import datetime, timezone
from stock_batch_expiry import classify_batch


def preview_fefo(*, now, requested_units, batches):
    """Suggest earliest-expiring batch allocations; flag unresolved quantities.

    Each batch is a mapping with id, units, manufacturer_use_by, and optional
    opened_at/post_open_discard. The caller must already have selected and
    authorized batches belonging to the same venue and ingredient.
    """
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('timezone-aware now required')
    if type(requested_units) is not int or not 0 < requested_units <= 1_000_000_000:
        raise ValueError('requested_units must be a bounded positive integer')
    if type(batches) not in (tuple, list) or len(batches) > 1000:
        raise ValueError('bounded batch collection required')
    eligible, excluded, seen = [], [], set()
    for batch in batches:
        if type(batch) is not dict:
            raise ValueError('batch mapping required')
        identifier, units = batch.get('id'), batch.get('units')
        if type(identifier) is not str or not identifier.strip() or identifier in seen:
            raise ValueError('unique nonempty batch id required')
        seen.add(identifier)
        if type(units) is not int or not 0 <= units <= 1_000_000_000:
            raise ValueError('bounded nonnegative batch units required')
        triage = classify_batch(now=now,
                                manufacturer_use_by=batch.get('manufacturer_use_by'),
                                opened_at=batch.get('opened_at'),
                                post_open_discard=batch.get('post_open_discard'))
        if triage['status'] != 'within_recorded_deadline':
            excluded.append({'batch_id': identifier, 'status': triage['status'],
                             'units': units})
        elif units:
            eligible.append((datetime.fromisoformat(triage['effective_deadline']), identifier, units))
    eligible.sort(key=lambda item: (item[0], item[1]))
    remaining, allocations = requested_units, []
    for deadline, identifier, units in eligible:
        quantity = min(units, remaining)
        if quantity:
            allocations.append({'batch_id': identifier, 'units': quantity,
                                'effective_deadline': deadline.astimezone(timezone.utc).isoformat()})
            remaining -= quantity
        if remaining == 0:
            break
    return {'allocations': allocations, 'unfulfilled_units': remaining,
            'excluded_batches': excluded, 'requires_manual_review': bool(excluded or remaining),
            'posted': False, 'reserved': False}
