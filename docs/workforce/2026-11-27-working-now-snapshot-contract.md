# 2026-11-27 — Who's Working Now: snapshot contract v0.1

Status: **offline architecture slice only**; not a deployed endpoint or verified integration. This increment is distinct from roster editing/publishing and live KPI work. GitHub develop README was readable, but the candidate Python API paths checked were absent; historical ZIP code was not verified.

## Boundary

Manager dashboard read: `GET /api/v1/manager/workforce/now` (proposed; not implemented). Server-side authenticated session supplies venue ID and manager permission; **never accept venue ID from query or body**. A missing session returns 401; insufficient manager grant returns 403. Do not reveal whether a different venue has a staff identifier. No public exposure until session, CSRF/origin, tenant and authorization gates are independently verified.

## Snapshot semantics

At an explicit timezone-aware `as_of` timestamp, return only shifts and fictional staff in the authorized venue. Each entry includes stable staff/shift identifiers, display name, station, scheduled start/end (ISO 8601 with offset), `scheduled_now`, `clocked_in`, and `presence_source`. `scheduled_now` means start <= as_of < end; **never infer presence from schedule**. `clocked_in` may be true only with a trusted kiosk punch-in not superseded by a later punch-out, scoped to the same venue/staff/shift. If the trusted punch stream is absent, report `clocked_in: null`, `presence_source: unavailable`, not false certainty. Future shifts are returned separately as `upcoming`. No mobile punches, tracking, disciplinary scores, medical details or payroll data.

## Testable acceptance criteria

1. Scheduled fictional worker without punch is not reported present.
2. Valid kiosk in/out toggles actual presence; late or duplicate events need deterministic reconciliation and immutable event IDs.
3. A manager for venue A cannot retrieve venue B shifts, staff or punches, even using guessed identifiers.
4. Unauthenticated and nonmanager reads are denied; venue comes only from session.
5. DST boundaries and naive timestamps are rejected or normalized with explicit timezone rules.
6. Missing punch data is marked unavailable; the UI must not display fake live headcounts.
7. No live customer/staff data, external notifications or network deployment.

## Next dependencies

Recover and inspect actual Python HTTP/storage modules and frontend integration before wiring a route. Add venue-owned shift/station/punch persistence, authenticated manager-only read, explicit data freshness, focused negative tests, then revision-checked weekly roster create/edit/publish. Coordinate with issue #4 and the separate React UI automation. Keep main untouched. €0 additional spend.
