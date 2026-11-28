"""Read-only waste preview backed by trusted venue-owned SQLite ingredient records.

Not an authenticated endpoint or posting command. Caller must authorize venue.
"""
from prototypes.inventory.inventory_ledger import balance, ident
from stock_waste_preview import preview_waste


def preview_waste_from_ledger(db, *, venue_id, ingredient_id, waste_units, reason, note=None):
    """Resolve unit and balance from the same venue; never trust client stock/unit."""
    venue_id, ingredient_id = ident(venue_id), ident(ingredient_id)
    row = db.execute(
        'SELECT unit FROM ingredients WHERE venue_id=? AND ingredient_id=?',
        (venue_id, ingredient_id),
    ).fetchone()
    if row is None:
        raise ValueError('ingredient not found in venue')
    current = balance(db, venue_id, ingredient_id)
    return preview_waste(
        venue_id=venue_id, sku_venue_id=venue_id, ledger_units=current,
        waste_units=waste_units, unit=row[0], reason=reason, note=note,
    )
