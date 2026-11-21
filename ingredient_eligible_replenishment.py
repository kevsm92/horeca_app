"""Offline, read-only ingredient/lot replenishment preview (synthetic use only).

Caller must supply authenticated, server-derived venue scope and a consistent
snapshot of trusted lot rows. This is NOT a database transaction or purchase API.
"""

def preview_ingredient_replenishment(*, venue_id, ingredient_id, unit, par_quantity, lots):
    for label, value in (("venue_id", venue_id), ("ingredient_id", ingredient_id), ("unit", unit)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"invalid_{label}")
    if type(par_quantity) is not int or par_quantity < 0:
        raise ValueError("invalid_quantity")
    if not isinstance(lots, (tuple, list)):
        raise ValueError("invalid_snapshot")
    eligible = 0
    revisions = []
    for lot in lots:
        if not isinstance(lot, dict):
            raise ValueError("invalid_snapshot")
        if lot.get("venue_id") != venue_id or lot.get("ingredient_id") != ingredient_id:
            raise PermissionError("scope_mismatch")
        if lot.get("unit") != unit:
            raise ValueError("unit_mismatch")
        on_hand, withheld, revision = (lot.get(k) for k in ("on_hand_quantity", "withheld_quantity", "revision"))
        if (type(on_hand) is not int or type(withheld) is not int or
                on_hand < 0 or withheld < 0 or withheld > on_hand):
            raise ValueError("invalid_quantity")
        if type(revision) is not int or revision < 1:
            raise ValueError("invalid_revision")
        status = lot.get("expiry_status")
        if status not in ("approved", "expired", "quarantined", "unverified"):
            raise ValueError("invalid_status")
        if status == "approved":
            eligible += on_hand - withheld
        revisions.append(revision)
    return {"venue_id": venue_id, "ingredient_id": ingredient_id, "unit": unit,
            "eligible_quantity": eligible,
            "suggested_quantity": max(0, par_quantity - eligible),
            "lot_revisions": revisions, "requires_human_review": True,
            "purchase_order_created": False, "ledger_modified": False}


if __name__ == "__main__":
    import unittest

    class PreviewTests(unittest.TestCase):
        def setUp(self):
            self.lot = dict(venue_id="fictional-v1", ingredient_id="fictional-i1", unit="g",
                            on_hand_quantity=7000, withheld_quantity=3000,
                            expiry_status="approved", revision=1)

        def preview(self, **kwargs):
            args = dict(venue_id="fictional-v1", ingredient_id="fictional-i1", unit="g",
                        par_quantity=10000, lots=[self.lot])
            args.update(kwargs)
            return preview_ingredient_replenishment(**args)

        def test_withheld(self):
            self.assertEqual(self.preview()["suggested_quantity"], 6000)

        def test_expired(self):
            self.assertEqual(self.preview(lots=[dict(self.lot, expiry_status="expired")])["eligible_quantity"], 0)

        def test_no_order(self):
            self.assertFalse(self.preview()["purchase_order_created"])

        def test_scope(self):
            for change in (dict(venue_id="other"), dict(ingredient_id="other")):
                with self.subTest(change=change), self.assertRaises(PermissionError):
                    self.preview(lots=[dict(self.lot, **change)])

        def test_invalid(self):
            for change in (dict(withheld_quantity=8000), dict(revision=0),
                           dict(unit="kg"), dict(expiry_status="unknown")):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    self.preview(lots=[dict(self.lot, **change)])

        def test_par_met(self):
            self.assertEqual(self.preview(par_quantity=4000)["suggested_quantity"], 0)

        def test_empty_snapshot(self):
            self.assertEqual(self.preview(lots=[])["suggested_quantity"], 10000)

        def test_boolean_quantity(self):
            with self.assertRaises(ValueError):
                self.preview(par_quantity=True)

    unittest.main()
