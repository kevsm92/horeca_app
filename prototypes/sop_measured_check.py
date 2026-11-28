"""Synthetic offline SOP check execution: acknowledgement is never a measured check."""
from dataclasses import dataclass
from datetime import datetime, timezone
import unittest

@dataclass(frozen=True)
class Check:
    venue: str
    sop_id: str
    revision: int
    actor: str
    observed_at: datetime
    result: str
    value: float | None = None
    unit: str | None = None
    instrument: str | None = None

    def __post_init__(self):
        if not all((self.venue, self.sop_id, self.actor)) or self.revision < 1:
            raise ValueError("invalid identity or revision")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("timezone-aware observation required")
        if self.result not in ("pass", "fail", "not_performed"):
            raise ValueError("invalid result")
        if self.result == "not_performed" and self.value is not None:
            raise ValueError("unperformed check cannot contain a measurement")
        if self.value is not None and (not self.unit or not self.instrument):
            raise ValueError("measured value requires unit and instrument")
        if self.result == "pass" and self.value is None:
            raise ValueError("pass requires measured evidence in this check type")

def record_check(check: Check, *, authorized_venue: str):
    if check.venue != authorized_venue:
        raise PermissionError("cross-venue check denied")
    return check

class Tests(unittest.TestCase):
    def setUp(self):
        self.t = datetime(2026, 11, 24, 20, tzinfo=timezone.utc)
        self.args = dict(venue="fictional-a", sop_id="chiller", revision=1,
                         actor="fictional-worker", observed_at=self.t)

    def test_measured_pass(self):
        c = Check(**self.args, result="pass", value=4.2, unit="C", instrument="synthetic-probe")
        self.assertIs(record_check(c, authorized_venue="fictional-a"), c)

    def test_no_click_through_pass(self):
        with self.assertRaises(ValueError):
            Check(**self.args, result="pass")

    def test_not_performed_cannot_fake_measurement(self):
        with self.assertRaises(ValueError):
            Check(**self.args, result="not_performed", value=4.2, unit="C", instrument="probe")

    def test_tenant_isolation(self):
        with self.assertRaises(PermissionError):
            record_check(Check(**self.args, result="fail"), authorized_venue="fictional-b")

    def test_naive_timestamp_denied(self):
        with self.assertRaises(ValueError):
            Check(**(self.args | {"observed_at": datetime(2026, 11, 24)}), result="fail")

if __name__ == "__main__":
    unittest.main()
