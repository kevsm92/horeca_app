"""Offline batch expiry triage for fictional inventory; no disposal or ledger writes.

Expiry is evaluated against a trusted, configured deadline, never inferred from
camera images. Unknown dates remain unresolved for human inspection.
"""
from datetime import datetime, timedelta


def preview_batch_expiry(*, inspected_at, discard_at=None, original_use_by=None,
                         warning_minutes=1440):
    """Classify a batch without extending its original use-by deadline."""
    if not isinstance(inspected_at, datetime) or inspected_at.tzinfo is None or inspected_at.utcoffset() is None:
        raise ValueError('inspected_at must be timezone-aware')
    for label, value in (('discard_at', discard_at), ('original_use_by', original_use_by)):
        if value is not None and (not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None):
            raise ValueError(f'{label} must be timezone-aware')
    if type(warning_minutes) is not int or not 0 <= warning_minutes <= 525600:
        raise ValueError('warning_minutes out of range')
    if discard_at is None and original_use_by is None:
        return {'status': 'unknown_deadline', 'effective_deadline': None,
                'requires_manual_review': True, 'disposed': False}
    deadline = min(x for x in (discard_at, original_use_by) if x is not None)
    if inspected_at >= deadline:
        status = 'expired'
    elif deadline - inspected_at <= timedelta(minutes=warning_minutes):
        status = 'expiring_soon'
    else:
        status = 'within_deadline'
    return {'status': status, 'effective_deadline': deadline,
            'requires_manual_review': status != 'within_deadline', 'disposed': False}
