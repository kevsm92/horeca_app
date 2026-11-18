import unittest
from recipe_allergen_review import review_allergens

class AllergenReviewTests(unittest.TestCase):
    def test_missing_recipe_fails_closed(self):
        self.assertFalse(review_allergens(None)['publishable'])
    def test_incomplete_supplier_data_fails_closed(self):
        result = review_allergens({'allergens':['milk'], 'allergen_status':'incomplete_supplier_verification'}, supplier_verified=True)
        self.assertEqual(result['status'], 'requires_supplier_review')
    def test_unverified_flag_fails_closed(self):
        self.assertFalse(review_allergens({'allergens':[], 'allergen_status':'supplier_verified'})['publishable'])
    def test_invalid_tags_fails_closed(self):
        self.assertEqual(review_allergens({'allergens':['milk',None]})['status'], 'invalid_metadata')
    def test_explicit_review_preserves_tags(self):
        r=review_allergens({'allergens':['soy','milk','soy'], 'allergen_status':'supplier_verified'},supplier_verified=True)
        self.assertEqual(r,{'status':'reviewed','publishable':True,'allergens':['milk','soy']})

if __name__ == '__main__': unittest.main()
