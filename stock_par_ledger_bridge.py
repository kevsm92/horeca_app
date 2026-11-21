"""Read-only, offline par suggestion from a venue-scoped ingredient ledger.

Ledger quantities are whole g/ml/each; par quantities use milliunits of the
same ingredient unit. Caller is responsible for authenticating venue access.
No supplier order or ledger mutation is performed.
"""
from stock_par_suggestions import suggest_replenishment


def suggest_from_ledger(db, *, venue_id, ingredient_id, par_milliunits,
                        reserved_milliunits=0, incoming_milliunits=0):
    """Return suggested milliunits for an existing ingredient in this venue.

    Reject overflow rather than silently allowing an oversized ledger balance.
    """
    from prototypes.inventory.inventory_ledger import balance

    units = balance(db, venue_id, ingredient_id)  # checks venue/ingredient pair
    if type(units) is not int or units < 0 or units > 1_000_000_000:
        raise ValueError('ledger balance outside supported milliunit range')
    return suggest_replenishment(
        on_hand_milliunits=units * 1000,
        reserved_milliunits=reserved_milliunits,
        par_milliunits=par_milliunits,
        incoming_milliunits=incoming_milliunits,
    )
