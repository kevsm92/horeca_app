import unittest
from kitchen_station_load import StationLine, station_load


class StationLoadTests(unittest.TestCase):
    def line(self, **changes):
        fields = dict(venue_id="fictional-a", ticket_id="t1", station="kitchen",
                      status="queued", item_id="soup", quantity=2)
        fields.update(changes)
        return StationLine(**fields)

    def test_aggregates_active_quantities_only(self):
        lines = [self.line(), self.line(ticket_id="t2", status="preparing", quantity=3),
                 self.line(ticket_id="t3", status="ready", quantity=1),
                 self.line(ticket_id="t4", status="served", quantity=9)]
        self.assertEqual(station_load(lines, authorized_venue_id="fictional-a", station="kitchen"),
                         {"queued": 2, "preparing": 3, "ready": 1})

    def test_tenant_and_station_isolation(self):
        lines = [self.line(venue_id="fictional-b", quantity=50),
                 self.line(station="bar", quantity=20)]
        self.assertEqual(station_load(lines, authorized_venue_id="fictional-a", station="kitchen"),
                         {"queued": 0, "preparing": 0, "ready": 0})

    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            station_load([self.line(), self.line()], authorized_venue_id="fictional-a", station="kitchen")

    def test_invalid_quantity_rejected(self):
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                station_load([self.line(quantity=value)], authorized_venue_id="fictional-a", station="kitchen")

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            station_load([self.line(status="unknown")], authorized_venue_id="fictional-a", station="kitchen")

    def test_invalid_scope_rejected(self):
        with self.assertRaises(ValueError):
            station_load([], authorized_venue_id="", station="kitchen")
        with self.assertRaises(ValueError):
            station_load([], authorized_venue_id="fictional-a", station="other")


if __name__ == "__main__":
    unittest.main()
