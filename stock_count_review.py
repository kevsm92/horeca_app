"""Offline stock-count review gate; no inventory adjustments are posted.

A variance is not physical evidence or permission to change the ledger.
Callers must authenticate the reviewer and authorize venue/role separately.
"""
from datetime import datetime
from stock_count_preview import preview_count


def review_count(*, ledger_units, counted_units, unit, counted_at, reviewed_at=None,
                 reviewer_id=None, reason=None):
    """Classify count discrepancy without approving or posting an adjustment."""
    preview = preview_count(ledger_units=ledger_units, counted_units=counted_units, unit=unit)
    if not isinstance(counted_at, datetime) or counted_at.tzinfo is None or counted_at.utcoffset() is None:
        raise ValueError('counted_at must be timezone-aware')
    if reviewed_at is not None and (not isinstance(reviewed_at, datetime) or reviewed_at.tzinfo is None
                                    or reviewed_at.utcoffset() is None or reviewed_at < counted_at):
        raise ValueError('reviewed_at must be timezone-aware and not before count')
    if not preview['requires_review']:
        return {**preview, 'status': 'matched', 'approved': False}
    if reviewed_at is None or not isinstance(reviewer_id, str) or not reviewer_id.strip() or not isinstance(reason, str) or not reason.strip():
        return {**preview, 'status': 'pending_review', 'approved': False}
    if len(reviewer_id) > 128 or len(reason) > 1000:
        raise ValueError('review metadata too long')
    return {**preview, 'status': 'review_documented', 'approved': False}
