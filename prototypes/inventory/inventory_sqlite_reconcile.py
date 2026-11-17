"""Read-only reconciliation adapter for the prototype integer-unit SQLite ledger.

Caller must authorize venue_id before use. No writes or external integrations.
"""
from inventory_reconciliation import reconcile_events


def reconcile_sqlite(db, venue_id):
    """Compare ordered stock events to SQL aggregates, including zero-stock items.

    Returns ingredient_id -> integer balance. Raises ValueError on discrepancies.
    When called outside a transaction, starts a read transaction to keep the
    ingredient, event, and aggregate queries on one SQLite snapshot. Existing
    caller transactions remain caller-owned.
    """
    if not isinstance(venue_id, str) or not venue_id:
        raise ValueError("invalid venue")
    owns_transaction = not db.in_transaction
    if owns_transaction:
        db.execute('BEGIN')
    try:
        result = _reconcile_snapshot(db, venue_id)
        if owns_transaction:
            db.commit()
        return result
    except BaseException:
        if owns_transaction:
            db.rollback()
        raise


def _reconcile_snapshot(db, venue_id):
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
