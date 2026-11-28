"""Immutable, venue-scoped BOM revision snapshots; offline only.

Snapshots preserve ingredient quantities/units, not verified allergen or supplier facts.
"""
import json

SCHEMA = """
CREATE TABLE IF NOT EXISTS recipe_revision_snapshots (
 venue_id TEXT NOT NULL CHECK(length(trim(venue_id))>0),
 recipe_id TEXT NOT NULL CHECK(length(trim(recipe_id))>0),
 revision INTEGER NOT NULL CHECK(revision>0),
 bom_json TEXT NOT NULL,
 PRIMARY KEY(venue_id,recipe_id,revision)
);
CREATE TRIGGER IF NOT EXISTS recipe_revision_no_update
BEFORE UPDATE ON recipe_revision_snapshots BEGIN SELECT RAISE(ABORT,'immutable revision'); END;
CREATE TRIGGER IF NOT EXISTS recipe_revision_no_delete
BEFORE DELETE ON recipe_revision_snapshots BEGIN SELECT RAISE(ABORT,'immutable revision'); END;
"""

def initialize(db):
    db.executescript(SCHEMA)

def publish(db, *, authorized_venue_id, recipe_id, revision):
    if not all(isinstance(v,str) and v.strip() for v in (authorized_venue_id,recipe_id)):
        raise ValueError('trusted venue and recipe required')
    if type(revision) is not int or revision < 1:
        raise ValueError('positive integer revision required')
    rows = db.execute("""SELECT c.ingredient_id,c.quantity,i.unit FROM recipe_components c
        JOIN recipe_ingredients i ON i.venue_id=c.venue_id AND i.ingredient_id=c.ingredient_id
        WHERE c.venue_id=? AND c.recipe_id=? ORDER BY c.ingredient_id""",
        (authorized_venue_id,recipe_id)).fetchall()
    if not rows:
        raise ValueError('cannot publish an empty or unknown recipe')
    bom = [{'ingredient_id':ingredient,'quantity':quantity,'unit':unit}
           for ingredient,quantity,unit in rows]
    with db:
        db.execute('INSERT INTO recipe_revision_snapshots VALUES (?,?,?,?)',
                   (authorized_venue_id,recipe_id,revision,json.dumps(bom,separators=(',',':'))))
    return bom

def read(db, *, authorized_venue_id, recipe_id, revision):
    if not all(isinstance(v,str) and v.strip() for v in (authorized_venue_id,recipe_id)):
        raise ValueError('trusted venue and recipe required')
    if type(revision) is not int or revision < 1:
        raise ValueError('positive integer revision required')
    row=db.execute('SELECT bom_json FROM recipe_revision_snapshots WHERE venue_id=? AND recipe_id=? AND revision=?',
                   (authorized_venue_id,recipe_id,revision)).fetchone()
    return json.loads(row[0]) if row else None
