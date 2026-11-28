# Manager weekly roster snapshot contract (2026-11-28, increment 1)

Status: **architecture contract only**. The accessible `develop` README does not establish a recoverable Python application, schema, authentication implementation, or test harness. Do not expose this as an HTTP route until those dependencies are inspected.

## Narrow milestone

Define a manager-only, venue-scoped, read-only weekly roster snapshot to support issue #4. This does **not** infer actual attendance from scheduled shifts.

Proposed endpoint: `GET /api/v1/manager/roster?week_start=YYYY-MM-DD`, where `week_start` must be a Monday in the venue's IANA timezone. Week boundaries are local Monday 00:00 inclusive through next Monday 00:00 exclusive, converted to UTC for database predicates (handle DST).

Response shape (illustrative, synthetic only):

```json
{
  "venue_id": "venue-fictional-a",
  "timezone": "Europe/Brussels",
  "week_start": "2026-11-30",
  "revision": 1,
  "generated_at": "2026-11-28T00:00:00Z",
  "shifts": [{
    "shift_id": "shift-fictional-1",
    "staff_id": "staff-fictional-1",
    "display_name": "Example Employee",
    "station_id": "station-fictional-kitchen",
    "starts_at": "2026-11-30T09:00:00+01:00",
    "ends_at": "2026-11-30T17:00:00+01:00",
    "roster_status": "draft",
    "attendance_status": "unknown"
  }]
}
```

## Non-negotiable enforcement

- Authenticate using a verified server-side session. Derive venue from authorized server session/grants; never trust client-supplied venue IDs.
- Require `manager:roster:read` for that venue; reject unauthenticated requests (401) and unauthorized principals (403). Return no roster rows from other venues.
- Use parameterized SQL with venue predicates on **every** staff, shift and station join. Do not reveal HR/absence reasons, earnings, contact details or payroll data.
- `attendance_status` must be sourced only from authorized factual kiosk punch events and may be `unknown`, `clocked_in`, or `clocked_out`; absence of a punch is **unknown**, not proof of absence. Scheduled shifts never imply presence.
- Revision is a monotonically increasing venue-week roster revision; future writes require atomic compare-and-swap, shift-overlap validation and audit provenance. No publish/write capability in this increment.
- On unavailable or unverified attendance source, return `unknown`; on unavailable roster source, return an explicit service error, never synthetic live metrics.
- Cache private data only with `Cache-Control: no-store`. Avoid logging personal identifiers in request telemetry.

## Acceptance checks for implementation follow-up

1. Two synthetic venues with overlapping staff/shift IDs: manager A reads only A; manager B reads only B.
2. No session => 401; non-manager => 403; forged venue query/header cannot change scope.
3. Shift scheduled but no kiosk punch => `unknown`; verified punch => factual state.
4. Monday validation, UTC boundary and Europe/Brussels DST transitions.
5. Repeated reads stable for unchanged revision; changed roster increments revision.
6. Staff/shift/station joins do not leak other-venue records; response contains no sensitive HR fields.

## Dependencies and backlog

First recover and inspect actual `develop` Python backend, session/authorization layer, migrations and tests before implementation. Next bounded increments: venue-week roster persistence and manager read endpoint; then safe draft edit/publish with revision conflicts; then operational KPI source inventory and authenticated aggregates with unavailable-data indicators. React UI belongs to separate frontend workstream. No deployment, real staff data, mobile punches, payments, communications or billed services.
