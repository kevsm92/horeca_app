"""Offline, venue-scoped par-level suggestions from validated eligible stock.

No procurement, inventory mutations or automated disposal. Quantities are
integer units of a single explicitly matched inventory item/unit.
"""


def preview_par_gap(*, venue_id, item_id, par_units, eligible_stock):
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue_id required')
    if not isinstance(item_id, str) or not item_id.strip():
        raise ValueError('item_id required')
    if type(par_units) is not int or par_units < 0:
        raise ValueError('par_units must be a nonnegative integer')
    if not isinstance(eligible_stock, dict):
        raise ValueError('eligible_stock must be a validated preview')
    if eligible_stock.get('venue_id') != venue_id:
        raise PermissionError('eligible stock venue mismatch')
    if eligible_stock.get('item_id') != item_id:
        raise ValueError('eligible stock item mismatch; never mix ingredients')
    eligible = eligible_stock.get('eligible_units')
    withheld = eligible_stock.get('withheld_units')
    if type(eligible) is not int or eligible < 0 or type(withheld) is not int or withheld < 0:
        raise ValueError('invalid eligible/withheld quantities')
    if eligible_stock.get('ledger_modified') is not False or eligible_stock.get('purchase_order_created') is not False:
        raise ValueError('stock preview must be read-only')
    return {
        'venue_id': venue_id, 'item_id': item_id, 'par_units': par_units,
        'eligible_units': eligible, 'withheld_units': withheld,
        'suggested_replenishment_units': max(0, par_units - eligible),
        'requires_human_review': withheld > 0,
        'purchase_order_created': False, 'ledger_modified': False,
    }
