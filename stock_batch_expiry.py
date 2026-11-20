"""Offline batch expiry triage; synthetic fixtures, not a food-safety determination.

All deadlines must come from a verified venue SOP/manufacturer record. No
universal shelf-life or temperature assumptions are embedded here.
"""
from datetime import datetime, timezone


def classify_batch(*, now, manufacturer_use_by, opened_at=None, post_open_discard=None):
    """Return a conservative review status; never extend manufacturer use-by.

    All supplied datetimes must be timezone-aware. An opened batch without an
    approved post-opening deadline is unresolved, never implicitly safe.
    """
    fields = (now, manufacturer_use_by, opened_at, post_open_discard)
    if any(x is not None and (not isinstance(x, datetime) or x.tzinfo is None
                              or x.utcoffset() is None) for x in fields):
        raise ValueError('timezone-aware datetimes required')
    if not isinstance(now, datetime) or not isinstance(manufacturer_use_by, datetime):
        raise ValueError('now and manufacturer deadline required')
    if opened_at is None and post_open_discard is not None:
        raise ValueError('post-opening deadline requires opening event')
    if opened_at is not None and opened_at > now:
        return {'status': 'untrusted_opening', 'effective_deadline': None,
                'requires_manual_review': True}
    if opened_at is not None and post_open_discard is None:
        return {'status': 'missing_post_open_rule', 'effective_deadline': None,
                'requires_manual_review': True}
    if post_open_discard is not None and post_open_discard < opened_at:
        return {'status': 'invalid_post_open_deadline', 'effective_deadline': None,
                'requires_manual_review': True}
    deadline = min(manufacturer_use_by, post_open_discard) if post_open_discard else manufacturer_use_by
    expired = now >= deadline
    return {'status': 'expired' if expired else 'within_recorded_deadline',
            'effective_deadline': deadline.astimezone(timezone.utc).isoformat(),
            'requires_manual_review': expired}
