"""Offline venue-scoped menu-to-recipe revision references.

The authenticated caller supplies a server-derived venue ID. This does not
verify recipe existence, ingredients, allergen declarations or cost.
"""
SCHEMA = """
CREATE TABLE IF NOT EXISTS menu_recipe_links (
 venue_id TEXT NOT NULL,
 item_id TEXT NOT NULL,
 recipe_id TEXT NOT NULL CHECK(length(trim(recipe_id))>0),
 recipe_revision INTEGER NOT NULL CHECK(recipe_revision>0),
 PRIMARY KEY (venue_id,item_id),
 FOREIGN KEY (venue_id,item_id) REFERENCES menu_items(venue_id,item_id) ON DELETE RESTRICT
);
"""

def initialize(db):
    db.executescript(SCHEMA)

def link_recipe(db, *, authorized_venue_id, item_id, recipe_id, recipe_revision):
    if not all(isinstance(x,str) and x.strip() for x in (authorized_venue_id,item_id,recipe_id)):
        raise ValueError('nonempty venue, item and recipe required')
    if type(recipe_revision) is not int or recipe_revision < 1:
        raise ValueError('positive integer revision required')
    with db:
        db.execute('INSERT INTO menu_recipe_links VALUES (?,?,?,?) '
                   'ON CONFLICT(venue_id,item_id) DO UPDATE SET '
                   'recipe_id=excluded.recipe_id, recipe_revision=excluded.recipe_revision',
                   (authorized_venue_id,item_id,recipe_id,recipe_revision))

def list_links(db, *, authorized_venue_id):
    if not isinstance(authorized_venue_id,str) or not authorized_venue_id.strip():
        raise ValueError('authorized venue required')
    return [dict(zip(('item_id','recipe_id','recipe_revision'),row)) for row in
            db.execute('SELECT item_id,recipe_id,recipe_revision FROM menu_recipe_links '
                       'WHERE venue_id=? ORDER BY item_id',(authorized_venue_id,))]
