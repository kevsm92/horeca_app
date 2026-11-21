"""Fail-closed offline allergen review gate for synthetic recipe summaries.

Not a legal compliance certificate or customer-facing allergen declaration.
"""

def review_allergens(summary, *, supplier_verified=False):
    """Return a conservative review decision without changing the source summary."""
    if summary is None or not isinstance(summary, dict):
        return {'status': 'unavailable', 'publishable': False, 'allergens': []}
    tags = summary.get('allergens')
    if not isinstance(tags, list) or any(not isinstance(t, str) or not t.strip() for t in tags):
        return {'status': 'invalid_metadata', 'publishable': False, 'allergens': []}
    normalized = sorted(set(tags))
    if summary.get('allergen_status') != 'supplier_verified' or supplier_verified is not True:
        return {'status': 'requires_supplier_review', 'publishable': False, 'allergens': normalized}
    return {'status': 'reviewed', 'publishable': True, 'allergens': normalized}
