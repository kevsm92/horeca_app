"""Manager-only boundary for offline weekly roster projections.

The principal must be created by a verified server authentication layer, never
from client-supplied venue or role headers. No HTTP exposure is provided here.
"""
from datetime import date, datetime
from roster_week import weekly_roster


def manager_weekly_roster(*, principal, shifts, monday: date, tz_name='Europe/Brussels'):
    if not getattr(principal, 'authenticated', False):
        raise PermissionError('authentication required')
    if getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authorization required')
    venue_id = getattr(principal, 'venue_id', None)
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise PermissionError('trusted venue required')
    if not isinstance(monday, date) or isinstance(monday, datetime):
        raise ValueError('week_start must be a date')
    result = weekly_roster(shifts, venue_id, monday, tz_name)
    result['access_scope'] = 'manager'
    return result
