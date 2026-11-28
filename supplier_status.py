"""Offline supplier activation gate; never sends orders or contacts suppliers."""

def set_supplier_active(db, *, venue_id, supplier_id, active):
    """Set supplier availability in one transaction; fail closed on missing venue row.

    Returns True only when a supplier in the specified venue exists. Inactive
    suppliers remain in the directory for historical purchase/quote references.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue_id required')
    if not isinstance(supplier_id, str) or not supplier_id.strip():
        raise ValueError('supplier_id required')
    if type(active) is not bool:
        raise ValueError('active must be boolean')
    with db:
        cursor = db.execute('UPDATE supplier SET active=? WHERE venue_id=? AND supplier_id=?',
                            (int(active), venue_id, supplier_id))
    return cursor.rowcount == 1
