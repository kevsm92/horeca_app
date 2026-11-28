"""Offline manager workforce presence projection; synthetic fixtures only.

Not an HTTP endpoint. Principal must originate from verified server authentication.
A scheduled shift is never proof of presence.
"""
from datetime import datetime, timezone


def working_now(*, principal, shifts, punches, as_of, punch_stream_available):
    if not getattr(principal, "authenticated", False):
        raise PermissionError("authentication required")
    if getattr(principal, "role", None) not in ("manager", "owner") or not getattr(principal, "venue_id", None):
        raise PermissionError("manager authorization required")
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    if type(punch_stream_available) is not bool:
        raise ValueError("punch stream availability required")
    venue = principal.venue_id
    now = as_of.astimezone(timezone.utc)
    result = []
    for shift in shifts:
        if shift["venue_id"] != venue:
            continue
        start, end = shift["start"], shift["end"]
        if any(d.tzinfo is None or d.utcoffset() is None for d in (start, end)):
            raise ValueError("shift times must be timezone-aware")
        if end <= start:
            raise ValueError("invalid shift interval")
        if end.astimezone(timezone.utc) <= now:
            continue
        scheduled = start.astimezone(timezone.utc) <= now
        relevant = []
        if punch_stream_available:
            for event in punches:
                if (event["venue_id"] != venue or event["staff_id"] != shift["staff_id"]
                        or event["shift_id"] != shift["id"]):
                    continue
                when = event["at"]
                if when.tzinfo is None or when.utcoffset() is None:
                    raise ValueError("punch time must be timezone-aware")
                if when.astimezone(timezone.utc) <= now:
                    if event["kind"] not in ("in", "out"):
                        raise ValueError("invalid punch kind")
                    relevant.append(event)
        relevant.sort(key=lambda e: (e["at"].astimezone(timezone.utc), e["id"]))
        # Conflicting same-time punch events cannot establish reliable presence.
        ambiguous = any(a["at"] == b["at"] and a["kind"] != b["kind"]
                        for a, b in zip(relevant, relevant[1:]))
        present = (None if not punch_stream_available or ambiguous else
                   (relevant[-1]["kind"] == "in" if relevant else False))
        result.append({"shift_id": shift["id"], "staff_id": shift["staff_id"],
                       "station": shift["station"], "scheduled_now": scheduled,
                       "clocked_in": present,
                       "presence_source": ("unavailable" if not punch_stream_available else
                                           "ambiguous" if ambiguous else "kiosk_events"),
                       "start": start.isoformat(), "end": end.isoformat()})
    result.sort(key=lambda row: (row["start"], row["shift_id"]))
    return {"as_of": as_of.isoformat(), "source": "offline_projection",
            "working": [r for r in result if r["scheduled_now"]],
            "upcoming": [r for r in result if not r["scheduled_now"]]}


if __name__ == "__main__":
    import unittest
    from datetime import timedelta
    from types import SimpleNamespace

    class PresenceTests(unittest.TestCase):
        def setUp(self):
            self.now = datetime(2026, 11, 27, 3, tzinfo=timezone.utc)
            self.manager = SimpleNamespace(authenticated=True, role="manager", venue_id="A")
            self.shift = dict(id="s1", staff_id="fictional-1", venue_id="A",
                              station="bar", start=self.now-timedelta(hours=1),
                              end=self.now+timedelta(hours=2))

        def project(self, **kwargs):
            args = dict(principal=self.manager, shifts=[self.shift], punches=[],
                        as_of=self.now, punch_stream_available=True)
            args.update(kwargs)
            return working_now(**args)

        def test_schedule_does_not_imply_presence(self):
            self.assertFalse(self.project()["working"][0]["clocked_in"])

        def test_unavailable_is_not_false(self):
            self.assertIsNone(self.project(punch_stream_available=False)["working"][0]["clocked_in"])

        def test_kiosk_in_out(self):
            event = dict(venue_id="A", staff_id="fictional-1", shift_id="s1",
                         at=self.now-timedelta(minutes=20), kind="in", id="p1")
            self.assertTrue(self.project(punches=[event])["working"][0]["clocked_in"])
            out = dict(event, id="p2", kind="out", at=self.now-timedelta(minutes=1))
            self.assertFalse(self.project(punches=[out, event])["working"][0]["clocked_in"])

        def test_tenant_isolation(self):
            self.assertEqual(self.project(shifts=[dict(self.shift, venue_id="B")])["working"], [])
            event = dict(venue_id="B", staff_id="fictional-1", shift_id="s1",
                         at=self.now, kind="in", id="p1")
            self.assertFalse(self.project(punches=[event])["working"][0]["clocked_in"])

        def test_denied(self):
            for p in (SimpleNamespace(authenticated=False, role="manager", venue_id="A"),
                      SimpleNamespace(authenticated=True, role="staff", venue_id="A")):
                with self.assertRaises(PermissionError):
                    self.project(principal=p)

        def test_ambiguous_events_fail_closed(self):
            base = dict(venue_id="A", staff_id="fictional-1", shift_id="s1", at=self.now)
            rows = [dict(base, kind="in", id="a"), dict(base, kind="out", id="b")]
            self.assertIsNone(self.project(punches=rows)["working"][0]["clocked_in"])

        def test_upcoming_and_invalid_clock(self):
            future = dict(self.shift, start=self.now+timedelta(hours=1),
                          end=self.now+timedelta(hours=3))
            self.assertEqual(len(self.project(shifts=[future])["upcoming"]), 1)
            with self.assertRaises(ValueError):
                self.project(as_of=datetime(2026, 11, 27, 3))

    unittest.main()
