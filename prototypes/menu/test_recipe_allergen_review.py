import unittest
from recipe_allergen_review import review_recipe_allergens as review

V = 'venue-fictional'
BOM = [{'ingredient_id': 'flour'}, {'ingredient_id': 'milk'}]


def entry(codes, *, venue=V, reviewed=True):
    return {'venue_id': venue, 'reviewed': reviewed, 'allergens': codes}


class AllergenReviewTests(unittest.TestCase):
    def test_reviewed_union_and_no_certification(self):
        result = review(BOM, authorized_venue_id=V, declarations={
            'flour': entry(['gluten_cereals']), 'milk': entry(['milk'])})
        self.assertEqual(result['declared_allergens'], ['gluten_cereals', 'milk'])
        self.assertEqual(result['review_status'], 'declarations_reviewed')
        self.assertFalse(result['allergen_free_certified'])

    def test_missing_ingredient_needs_review(self):
        result = review(BOM, authorized_venue_id=V, declarations={
            'flour': entry(['gluten_cereals'])})
        self.assertEqual(result['unresolved_ingredient_ids'], ['milk'])
        self.assertEqual(result['review_status'], 'needs_review')

    def test_unreviewed_still_discloses_known_allergen(self):
        result = review([BOM[0]], authorized_venue_id=V, declarations={
            'flour': entry(['gluten_cereals'], reviewed=False)})
        self.assertEqual(result['declared_allergens'], ['gluten_cereals'])
        self.assertEqual(result['review_status'], 'needs_review')

    def test_empty_codes_not_allergen_free(self):
        result = review([BOM[0]], authorized_venue_id=V, declarations={
            'flour': entry([])})
        self.assertFalse(result['allergen_free_certified'])

    def test_cross_venue_rejected(self):
        with self.assertRaises(ValueError):
            review([BOM[0]], authorized_venue_id=V, declarations={
                'flour': entry([], venue='other')})

    def test_unknown_code_rejected(self):
        with self.assertRaises(ValueError):
            review([BOM[0]], authorized_venue_id=V, declarations={
                'flour': entry(['invented'])})

    def test_duplicate_ingredient_rejected(self):
        with self.assertRaises(ValueError):
            review([BOM[0], BOM[0]], authorized_venue_id=V, declarations={})

    def test_invalid_venue_rejected(self):
        with self.assertRaises(ValueError):
            review([BOM[0]], authorized_venue_id=' ', declarations={})


if __name__ == '__main__':
    unittest.main()
