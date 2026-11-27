"""Offline manager-only roster revision diff; no persistence or notifications.

Caller must provide server-loaded snapshots and authenticated principal.
"""


def preview_roster_changes(*, principal, before, after):
    if not getattr(principal, "authenticated", False) or getattr(principal, "role", None) not in ("manager", "owner"):
        raise PermissionError("manager authentication required")
    venue = getattr(principal, "venue_id", None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError("trusted venue required")
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ValueError("snapshots required")
    if before.get("venue_id") != venue or after.get("venue_id") != venue:
        raise PermissionError("cross-venue snapshot")
    if before.get("week_start") != after.get("week_start") or not isinstance(before.get("week_start"), str):
        raise ValueError("week mismatch")

    def index(snapshot):
        shifts = snapshot.get("shifts")
        if not isinstance(shifts, list):
            raise ValueError("shift list required")
        result = {}
        for shift in shifts:
            if not isinstance(shift, dict) or not isinstance(shift.get("id"), str) or not shift["id"]:
                raise ValueError("invalid shift")
            if shift.get("venue_id") != venue or shift["id"] in result:
                raise ValueError("cross-venue or duplicate shift")
            result[shift["id"]] = shift
        return result

    old, new = index(before), index(after)
    return {"venue_id": venue, "week_start": before["week_start"],
            "added": sorted(new.keys() - old.keys()),
            "removed": sorted(old.keys() - new.keys()),
            "changed": sorted(k for k in old.keys() & new.keys() if old[k] != new[k]),
            "unchanged_count": sum(old[k] == new[k] for k in old.keys() & new.keys()),
            "source": "offline_roster_diff", "persisted": False}


if __name__ == "__main__":
    import unittest
    from types import SimpleNamespace

    class PreviewTests(unittest.TestCase):
        def setUp(self):
            self.manager = SimpleNamespace(authenticated=True, role="manager", venue_id="fictional-a")
            self.before = {"venue_id": "fictional-a", "week_start": "2026-11-23", "shifts": [
                {"id": "a", "venue_id": "fictional-a", "station": "bar"},
                {"id": "b", "venue_id": "fictional-a", "station": "kitchen"}]}
            self.after = {"venue_id": "fictional-a", "week_start": "2026-11-23", "shifts": [
                {"id": "a", "venue_id": "fictional-a", "station": "floor"},
                {"id": "c", "venue_id": "fictional-a", "station": "kitchen"}]}

        def test_diff_and_no_mutation(self):
            import copy
            original = copy.deepcopy(self.after)
            result = preview_roster_changes(principal=self.manager, before=self.before, after=self.after)
            self.assertEqual((result["added"], result["removed"], result["changed"]), (["c"], ["b"], ["a"]))
            self.assertFalse(result["persisted"])
            self.assertEqual(self.after, original)

        def test_denied_staff_and_unauthenticated(self):
            for role, authenticated in [("staff", True), ("manager", False)]:
                with self.subTest(role=role, authenticated=authenticated), self.assertRaises(PermissionError):
                    preview_roster_changes(principal=SimpleNamespace(role=role, authenticated=authenticated, venue_id="fictional-a"), before=self.before, after=self.after)

        def test_cross_venue_and_shift_rejected(self):
            for bad in [dict(self.after, venue_id="fictional-b"),
                        dict(self.after, shifts=[{"id": "a", "venue_id": "fictional-b"}])]:
                with self.assertRaises((PermissionError, ValueError)):
                    preview_roster_changes(principal=self.manager, before=self.before, after=bad)

        def test_duplicate_and_week_mismatch(self):
            for bad in [dict(self.after, shifts=self.after["shifts"] * 2),
                        dict(self.after, week_start="2026-11-30")]:
                with self.assertRaises(ValueError):
                    preview_roster_changes(principal=self.manager, before=self.before, after=bad)

    unittest.main(verbosity=2)
