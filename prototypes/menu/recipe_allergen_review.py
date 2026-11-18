"""Conservative offline allergen review for published recipe BOMs.

Ingredient declarations are venue-reviewed inputs, not legal certification.
Missing or unreviewed declarations prevent complete review. Cross-contact
and 'allergen-free' claims are never inferred from declarations.
"""

EU_ALLERGEN_CODES = frozenset({
    'gluten_cereals', 'crustaceans', 'eggs', 'fish', 'peanuts', 'soybeans',
    'milk', 'nuts', 'celery', 'mustard', 'sesame', 'sulphites', 'lupin', 'molluscs',
})


def review_recipe_allergens(bom, *, authorized_venue_id, declarations):
    """Aggregate declared codes; fail closed on missing or unreviewed ingredients.

    bom: validated list of dicts with ingredient_id.
    declarations: ingredient_id -> {'venue_id', 'reviewed', 'allergens'}.
    """
    if not isinstance(authorized_venue_id, str) or not authorized_venue_id.strip():
        raise ValueError('trusted venue required')
    if not isinstance(bom, list) or not bom or not isinstance(declarations, dict):
        raise ValueError('validated nonempty BOM and declarations required')
    declared = set()
    unresolved = set()
    seen = set()
    for line in bom:
        if not isinstance(line, dict):
            raise ValueError('invalid BOM line')
        ingredient = line.get('ingredient_id')
        if not isinstance(ingredient, str) or not ingredient.strip() or ingredient in seen:
            raise ValueError('invalid or duplicate ingredient')
        seen.add(ingredient)
        record = declarations.get(ingredient)
        if record is None:
            unresolved.add(ingredient)
            continue
        if not isinstance(record, dict) or record.get('venue_id') != authorized_venue_id:
            raise ValueError('cross-venue or malformed allergen declaration')
        codes = record.get('allergens')
        if not isinstance(codes, (list, tuple, set, frozenset)) or any(
            not isinstance(code, str) or code not in EU_ALLERGEN_CODES for code in codes
        ):
            raise ValueError('invalid allergen codes')
        declared.update(codes)
        if record.get('reviewed') is not True:
            unresolved.add(ingredient)
    return {
        'declared_allergens': sorted(declared),
        'unresolved_ingredient_ids': sorted(unresolved),
        'review_status': 'needs_review' if unresolved else 'declarations_reviewed',
        'allergen_free_certified': False,
    }
