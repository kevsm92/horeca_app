"""Read-only, venue-bound supplier SKU resolution for offline purchasing drafts."""

def resolve_supplier_sku(db, *, venue_id, supplier_id, sku):
    """Return a fictional supplier SKU snapshot or None; never fall back across venues.

    Inactive suppliers are excluded from new purchasing choices. This lookup
    does not authorize purchasing or reserve stock.
    """
    for field, value in (("venue_id", venue_id), ("supplier_id", supplier_id), ("sku", sku)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a nonempty string")
    row = db.execute("""SELECT k.ingredient_id, k.unit, k.pack_quantity,
                               k.price_cents, k.lead_days, k.currency
                        FROM supplier_sku AS k JOIN supplier AS s
                          ON s.venue_id=k.venue_id AND s.supplier_id=k.supplier_id
                        WHERE k.venue_id=? AND k.supplier_id=? AND k.sku=?
                          AND s.active=1""", (venue_id, supplier_id, sku)).fetchone()
    if row is None:
        return None
    ingredient_id, unit, pack_quantity, price_cents, lead_days, currency = row
    return {"supplier_id": supplier_id, "sku": sku, "ingredient_id": ingredient_id,
            "unit": unit, "pack_quantity": pack_quantity, "price_cents": price_cents,
            "lead_days": lead_days, "currency": currency}
