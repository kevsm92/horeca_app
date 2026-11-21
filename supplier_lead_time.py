"""Offline supplier lead-time eligibility preview; never places orders.

Uses the venue-filtered, active-supplier directory. A quote is eligible only
when its configured whole-day lead time fits a caller-provided horizon.
No calendar, holiday or delivery promise is inferred from this estimate.
"""
from supplier_directory import list_skus


def eligible_supplier_skus(db, venue_id, ingredient_id, max_lead_days):
    """Return matching directory rows sorted by lead time, then stable IDs."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue_id is required')
    if not isinstance(ingredient_id, str) or not ingredient_id.strip():
        raise ValueError('ingredient_id is required')
    if type(max_lead_days) is not int or not 0 <= max_lead_days <= 365:
        raise ValueError('max_lead_days must be an integer from 0 to 365')
    rows = list_skus(db, venue_id, ingredient_id)
    return sorted((row for row in rows if row[6] <= max_lead_days),
                  key=lambda row: (row[6], row[0], row[2]))
