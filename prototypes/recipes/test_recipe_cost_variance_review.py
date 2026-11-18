"""Synthetic-only regression checks for review-only cost variance."""
import unittest
from recipe_cost_variance_review import assess_cost_variance


def quote(cents, *, venue="fictional-bistro", revision=1, recipe="soup"):
    return {"venue_id": venue, "quote_revision": revision, "recipe_id": recipe,
            "approved_yield": 2, "estimated_batch_cost_cents": cents,
            "estimated_portion_costs_cents": [cents // 2 + cents % 2, cents // 2]}


class CostVarianceReviewTests(unittest.TestCase):
    def test_threshold_boundary_and_no_auto_approval(self):
        result = assess_cost_variance(quote(100), quote(110, revision=2),
                                      authorized_venue="fictional-bistro",
                                      review_threshold_cents=10)
        self.assertTrue(result["requires_manager_review"])
        self.assertEqual(result["approval_status"], "not_approved")
        self.assertEqual(result["effect"], "review_only_no_price_or_stock_mutation")

    def test_zero_threshold_requires_actual_cost_change(self):
        for current_cost, expected in ((100, False), (101, True), (99, True)):
            with self.subTest(current_cost=current_cost):
                result = assess_cost_variance(
                    quote(100), quote(current_cost, revision=2),
                    authorized_venue="fictional-bistro", review_threshold_cents=0)
                self.assertEqual(result["requires_manager_review"], expected)
                self.assertEqual(result["approval_status"], "not_approved")

    def test_below_threshold_and_negative_variance(self):
        for end, expected in ((109, False), (90, True)):
            with self.subTest(end=end):
                result = assess_cost_variance(quote(100), quote(end, revision=2),
                                              authorized_venue="fictional-bistro",
                                              review_threshold_cents=10)
                self.assertEqual(result["requires_manager_review"], expected)

    def test_rejects_cross_venue_and_missing_provenance(self):
        for changed in (quote(110, venue="other", revision=2),
                        {k: v for k, v in quote(110, revision=2).items() if k != "venue_id"}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                assess_cost_variance(quote(100), changed, authorized_venue="fictional-bistro",
                                     review_threshold_cents=10)

    def test_rejects_replayed_or_invalid_revision(self):
        for revision in (1, 0, True, "2"):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                assess_cost_variance(quote(100), quote(110, revision=revision),
                                     authorized_venue="fictional-bistro", review_threshold_cents=10)

    def test_rejects_invalid_threshold_and_yield(self):
        for threshold in (-1, True, 1.5):
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                assess_cost_variance(quote(100), quote(110, revision=2),
                                     authorized_venue="fictional-bistro", review_threshold_cents=threshold)
        with self.assertRaises(ValueError):
            assess_cost_variance(quote(100), quote(110, revision=2, recipe="other"),
                                 authorized_venue="fictional-bistro", review_threshold_cents=10)


if __name__ == "__main__":
    unittest.main()
