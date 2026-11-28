"""Offline freshness annotation for manager KPI snapshots (not a live API).

A stale observation must never be represented as live, nor silently zeroed.
The caller supplies a trusted observation timestamp and explicit freshness policy.
"""
from datetime import datetime, timedelta, timezone


def annotate_freshness(*, snapshot, observed_at, as_of, max_age_seconds=300):
    if not isinstance(snapshot, dict) or snapshot.get('is_live') is not False:
        raise ValueError('only explicitly offline snapshots are supported')
    if type(max_age_seconds) is not int or not 1 <= max_age_seconds <= 86400:
        raise ValueError('invalid freshness threshold')
    for instant in (observed_at, as_of):
        if not isinstance(instant, datetime) or instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError('aware timestamps required')
    age = as_of.astimezone(timezone.utc) - observed_at.astimezone(timezone.utc)
    if age < timedelta(0):
        raise ValueError('observation cannot be in the future')
    if not isinstance(snapshot.get('venue_id'), str) or not snapshot['venue_id'].strip():
        raise ValueError('trusted venue required')
    return {**snapshot, 'freshness': {
        'status': 'stale' if age > timedelta(seconds=max_age_seconds) else 'recent_offline',
        'observed_at_utc': observed_at.astimezone(timezone.utc).isoformat(),
        'checked_at_utc': as_of.astimezone(timezone.utc).isoformat(),
        'age_seconds': int(age.total_seconds()),
        'threshold_seconds': max_age_seconds,
    }, 'is_live': False}
