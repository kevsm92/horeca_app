"""Offline venue-scoped recipe/BOM cost estimate; no stock movements or allergen certification."""
SCHEMA = """
CREATE TABLE IF NOT EXISTS recipe_ingredients (
 venue_id TEXT NOT NULL, ingredient_id TEXT NOT NULL,
 unit TEXT NOT NULL CHECK(unit IN ('mg','ml','piece')),
 cost_cents_per_1000 INTEGER NOT NULL CHECK(cost_cents_per_1000>=0),
 allergens TEXT NOT NULL DEFAULT '',
 PRIMARY KEY(venue_id,ingredient_id));
CREATE TABLE IF NOT EXISTS recipe_components (
 venue_id TEXT NOT NULL, recipe_id TEXT NOT NULL, ingredient_id TEXT NOT NULL,
 quantity INTEGER NOT NULL CHECK(quantity>0),
 PRIMARY KEY(venue_id,recipe_id,ingredient_id),
 FOREIGN KEY(venue_id,ingredient_id) REFERENCES recipe_ingredients(venue_id,ingredient_id));
"""
def initialize(db):
    db.executescript(SCHEMA)
def add_ingredient(db, *, venue, ingredient, unit, cost_cents_per_1000, allergens=()):
    if not isinstance(venue,str) or not venue.strip() or not isinstance(ingredient,str) or not ingredient.strip():
        raise ValueError('venue and ingredient required')
    if unit not in ('mg','ml','piece') or type(cost_cents_per_1000) is not int or cost_cents_per_1000<0:
        raise ValueError('invalid unit or cost')
    if not isinstance(allergens,(tuple,list)) or any(not isinstance(a,str) or not a.strip() or ',' in a for a in allergens):
        raise ValueError('invalid allergen metadata')
    with db:
        db.execute('INSERT INTO recipe_ingredients VALUES (?,?,?,?,?)',
                   (venue,ingredient,unit,cost_cents_per_1000,','.join(sorted(set(allergens)))))
def add_component(db, *, venue, recipe, ingredient, quantity, unit):
    if not all(isinstance(v,str) and v.strip() for v in (venue,recipe,ingredient)) or type(quantity) is not int or quantity<=0:
        raise ValueError('invalid component')
    row=db.execute('SELECT unit FROM recipe_ingredients WHERE venue_id=? AND ingredient_id=?',
                   (venue,ingredient)).fetchone()
    if row is None or row[0]!=unit:
        raise ValueError('unknown ingredient or incompatible unit')
    with db:
        db.execute('INSERT INTO recipe_components VALUES (?,?,?,?)',(venue,recipe,ingredient,quantity))
def recipe_summary(db, *, authorized_venue, recipe):
    if not all(isinstance(v,str) and v.strip() for v in (authorized_venue,recipe)):
        raise ValueError('trusted venue and recipe required')
    rows=db.execute('''SELECT c.ingredient_id,c.quantity,i.unit,i.cost_cents_per_1000,i.allergens
      FROM recipe_components c JOIN recipe_ingredients i
      ON i.venue_id=c.venue_id AND i.ingredient_id=c.ingredient_id
      WHERE c.venue_id=? AND c.recipe_id=? ORDER BY c.ingredient_id''',
      (authorized_venue,recipe)).fetchall()
    if not rows:
        return None
    numerator=sum(q*cost for _,q,_,cost,_ in rows)
    return {'recipe_id':recipe,'estimated_cost_cents':(numerator+999)//1000,
            'allergens':sorted({a for *_,tags in rows for a in tags.split(',') if a}),
            'components':[{'ingredient_id':name,'quantity':q,'unit':unit} for name,q,unit,_,_ in rows],
            'allergen_status':'incomplete_supplier_verification'}
