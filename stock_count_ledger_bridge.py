"""Read-only stock-count variance from venue-scoped SQLite ingredient ledger.

Caller must authenticate and authorize the venue. This is not a physical count
attestation, approval, or stock adjustment. No writes are performed.
"""
from prototypes.inventory.inventory_ledger import balance, ident
from stock_count_preview import preview_count


def preview_count_from_ledger(db, *, venue_id, ingredient_id, counted_units):
    """Use trusted unit and ledger balance; never accept client stock or unit."""
    venue_id, ingredient_id = ident(venue_id), ident(ingredient_id)
    row = db.execute(
        'SELECT unit FROM ingredients WHERE venue_id=? AND ingredient_id=?',
        (venue_id, ingredient_id),
    ).fetchone()
    if row is None:
        raise ValueError('ingredient not found in venue')
    current = balance(db, venue_id, ingredient_id)
    return preview_count(ledger_units=current, counted_units=counted_units,
                         unit=row[0])
