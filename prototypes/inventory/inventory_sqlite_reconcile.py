"""Read-only reconciliation adapter for the prototype integer-unit SQLite ledger.

Caller must authorize venue_id before use. No writes or external integrations.
"""
from inventory_reconciliation import reconcile_events


def reconcile_sqlite(db, venue_id):
    """Compare ordered stock events to SQL aggregates, including zero-stock items.

    Returns ingredient_id -> integer balance. Raises ValueError on discrepancies.
    Caller should provide a stable SQLite snapshot/transaction if concurrent
    writers are possible; this function never starts or commits transactions.
    """
    if not isinstance(venue_id, str) or not venue_id:
        raise ValueError("invalid venue")
    ingredients = {
        row[0] for row in db.execute(
            "SELECT ingredient_id FROM ingredients WHERE venue_id=?", (venue_id,)
        )
    }
    events = [
        dict(venue_id=venue_id, event_id=key, ingredient_id=ingredient,
             delta=delta, reason=reason)
        for key, ingredient, delta, reason in db.execute(
            "SELECT event_id, ingredient_id, delta, reason FROM stock_events "
            "WHERE venue_id=? ORDER BY rowid", (venue_id,)
        )
    ]
    for event in events:
        if event["ingredient_id"] not in ingredients:
            raise ValueError("event references missing ingredient")
    computed = reconcile_events(events, venue_id)
    sql_balances = dict(db.execute(
        "SELECT ingredient_id, COALESCE(SUM(delta),0) FROM stock_events "
        "WHERE venue_id=? GROUP BY ingredient_id", (venue_id,)
    ))
    if computed != sql_balances:
        raise ValueError("ledger reconciliation mismatch")
    return {ingredient: computed.get(ingredient, 0) for ingredient in sorted(ingredients)}
