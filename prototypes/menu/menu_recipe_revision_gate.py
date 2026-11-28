"""Offline guard for menu-to-recipe revision references; no allergen certification."""
from bom_validation import validate_bom_snapshot

def resolve_published_recipe(db, *, authorized_venue_id, item_id):
    """Return a venue-matched immutable BOM snapshot, or None if unlinked.

    Fail closed if a link points at an unpublished revision. Caller must derive
    authorized_venue_id from its authenticated session, never request input.
    """
    if not all(isinstance(x, str) and x.strip() for x in (authorized_venue_id, item_id)):
        raise ValueError('trusted venue and item required')
    row = db.execute('''SELECT l.recipe_id,l.recipe_revision,s.bom_json
      FROM menu_recipe_links l LEFT JOIN recipe_revision_snapshots s
      ON s.venue_id=l.venue_id AND s.recipe_id=l.recipe_id
         AND s.revision=l.recipe_revision
      WHERE l.venue_id=? AND l.item_id=?''', (authorized_venue_id,item_id)).fetchone()
    if row is None:
        return None
    if row[2] is None:
        raise ValueError('linked recipe revision is not published')
    bom = validate_bom_snapshot(row[2])
    return {'recipe_id':row[0], 'recipe_revision':row[1], 'bom':bom,
            'allergen_status':'unverified', 'cost_status':'not_quoted'}
