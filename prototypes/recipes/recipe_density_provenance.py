"""Read-only provenance for recipe mass/volume density approvals (offline prototype).

A provenance lookup is NOT a legal food-safety approval and never changes a BOM.
Caller supplies the authenticated server-derived venue, not a client venue field.
"""
def density_approval_provenance(db, *, authorized_venue, ingredient_id):
    if not isinstance(authorized_venue, str) or not authorized_venue.strip():
        raise ValueError('trusted venue required')
    if not isinstance(ingredient_id, str) or not ingredient_id.strip():
        raise ValueError('ingredient required')
    row = db.execute(
        """SELECT revision,status,mg_per_ml_numerator,mg_per_ml_denominator
           FROM ingredient_density_revisions
           WHERE venue_id=? AND ingredient_id=?
           ORDER BY revision DESC LIMIT 1""",
        (authorized_venue, ingredient_id),
    ).fetchone()
    if row is None:
        return {'ingredient_id': ingredient_id, 'usable': False, 'reason': 'missing',
                'revision': None}
    revision, status, numerator, denominator = row
    if status != 'approved':
        return {'ingredient_id': ingredient_id, 'usable': False, 'reason': 'revoked',
                'revision': revision}
    return {'ingredient_id': ingredient_id, 'usable': True, 'reason': 'approved',
            'revision': revision, 'mg_per_ml_numerator': numerator,
            'mg_per_ml_denominator': denominator}
