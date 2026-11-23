# HORECA role-specific frontends and HORECA Time architecture v1.1

Status: APPROVED ARCHITECTURE / IMPLEMENTATION BACKLOG
Date: 2026-11-23
Branch: develop
Constraints: synthetic data only, €0 incremental spending, no live payroll, real employee data, external communications, paid services, or real attendance capture.

## Decisions
- Role-specific React workspaces for floor/service, kitchen/bar, shift manager, owner/admin and limited personal staff self-service. Share UI components, identity, permission contracts and API client; do not create separate deployable frontends prematurely.
- HORECA Time is a separate modular monolith with separate Python API, SQLite database, kiosk frontend and deployment boundary. Main HORECA owns scheduling; Time owns actual attendance and corrections.
- Clock in, clock out and break punches occur **only on venue-bound shared kiosks**. No employee mobile punching. Optional staff portal can show history and submit corrections, but not punch.
- Only opening/closing, compliance and exception tasks; no generic tickets for routine table or kitchen work. Station/role assignment preferred, individual assignment when needed.
- Preserve existing main/develop branch policy, menu-first integration, €0 additional spend, synthetic fixtures and existing feature milestones.

## Role shells
- /floor: table map, reservations, POS and contextual station checks.
- /kitchen: KDS, prep states, allergens, critical safety exceptions.
- /manager: Who's Working Now (scheduled vs actual), coverage gaps, approvals, exception review.
- /admin: venue configuration, purchasing, reports, role management.
- /staff: personal schedule, read-only time history and correction requests.
- /time-kiosk: separately served application with venue-bound kiosk identity.

Backend authorization is authoritative. Roles grant capabilities, and each capability is restricted to the appropriate business/venue. Shared devices never inherit employee or manager sessions.

## Time domain and integrity
Entities: time_kiosks, time_employee_refs, attendance_events, attendance_sessions, break_intervals, time_correction_requests, time_correction_reviews, time_audit_events, time_outbox.
States: CLOCKED_OUT -> WORKING -> ON_BREAK -> WORKING -> CLOCKED_OUT.
Attendance is an append-only, server-timestamped event log; never overwrite punches. Corrections append reviewed adjustments. Unique event and idempotency keys prevent duplicate punches. Server rejects impossible transitions and overlapping open attendance sessions according to explicit policy. Use SQLite transactions and auditable reason codes.
Kiosk authentication combines provisioned device credential with staff PIN or authorized badge, with rate limiting, short-lived sessions, no exposure of PINs, inactivity reset, no employee data after completion, and device revocation. Offline punching must not silently create authoritative timestamps; initially fail closed with clear outage indication.

## Proposed APIs
POST /api/v1/time/kiosks/register (admin provision)
POST /api/v1/time/punches/clock-in
POST /api/v1/time/punches/break-start
POST /api/v1/time/punches/break-end
POST /api/v1/time/punches/clock-out
GET /api/v1/time/me/summary (read-only)
POST /api/v1/time/corrections
POST /api/v1/time/corrections/{id}/review
GET /api/v1/time/manager/attendance

The main app consumes versioned outbox events time.employee_clocked_in.v1, time.employee_break_started.v1, time.employee_break_ended.v1, time.employee_clocked_out.v1, time.attendance_corrected.v1. The projection exposes freshness; stale data is never presented as live attendance. No cross-database writes.

## Tasks
Opening/closing: shift- or station-triggered checklists.
Compliance: explicit measurements, evidence, required SOP revision and review; ticking complete is not proof of compliance.
Exceptions: deviations from normal operation with owner, urgency, resolution and audit history.
Avoid converting normal POS/KDS work into tasks. Pilot on synthetic flows and measure staff interaction overhead.

## Implementation integration
- 2026-11-24 to 26: role route/permission contracts and limited task taxonomy, only after checking existing implementations.
- 2026-11-27 to Dec: manager attendance projection and separate Time domain foundation.
- Dec 2026 to Jan 2027: synthetic kiosk punches, breaks, append-only events, corrections.
- Feb to Mar 2027: security, manager approvals, projection sync, checklist pilot.
- Apr to Jul 2027: integrate role-specific shells progressively around existing menu/tables/KDS contracts.
- Aug to Oct 2027: loyalty issue #2 remains a distinct late-2027 workstream.

## Acceptance tests
- Unauthorized roles/venues cannot see or mutate attendance.
- Kiosk can clock in/out and record breaks for synthetic staff; duplicate requests do not create duplicate events.
- Invalid transitions, PIN brute force, device revocation and stale projection fail safely.
- Employee correction requests and manager reviews are audited; raw punch history unchanged.
- No personal-device punch endpoint or real employee information.
- No paid services, external messages, official reporting or payroll transactions.
- Existing menu/table integrations and scheduled milestones remain unaffected.

Before any real use: Belgian labor/payroll/privacy and mandatory reporting review; no inference that Time punch equals Dimona declaration.
