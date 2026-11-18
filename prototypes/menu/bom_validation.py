"""Strict offline validation for synthetic recipe BOM snapshots.

Quantities are integer minor units; conversion factors belong to a separately
approved, versioned conversion table. This module does not infer allergens.
"""

import json

ALLOWED_UNITS = frozenset({'mg', 'ml', 'count'})


def validate_bom_snapshot(raw_json):
    """Return validated components, failing closed on malformed BOMs.

    Caller must first authorize the venue and recipe revision. Never accept
    this validator as proof of food-safety, ingredient identity or allergen status.
    """
    try:
        components = json.loads(raw_json)
    except (TypeError, ValueError) as exc:
        raise ValueError('invalid BOM JSON') from exc
    if not isinstance(components, list) or not components:
        raise ValueError('BOM must contain components')
    seen = set()
    for component in components:
        if not isinstance(component, dict) or set(component) != {'ingredient_id', 'quantity', 'unit'}:
            raise ValueError('invalid component fields')
        ingredient = component['ingredient_id']
        quantity = component['quantity']
        unit = component['unit']
        if not isinstance(ingredient, str) or not ingredient.strip() or ingredient != ingredient.strip():
            raise ValueError('invalid ingredient identifier')
        if ingredient in seen:
            raise ValueError('duplicate ingredient identifier')
        seen.add(ingredient)
        if type(quantity) is not int or not 0 < quantity <= 1_000_000_000:
            raise ValueError('quantity must be a positive bounded integer')
        if unit not in ALLOWED_UNITS:
            raise ValueError('unsupported unit')
    return components
