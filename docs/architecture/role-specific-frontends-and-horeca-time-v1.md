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

## Shift-triggered configurable task assignments (v1.2 extension)
**Purpose:** give an individually accountable set of opening/closing, compliance and exception tasks to the employee rostered for a qualifying shift, while keeping normal POS/KDS work out of the task engine.

### Configuration
A manager creates versioned `task_templates` and `task_template_items` scoped to business, venue, station, role/capability, shift kind (OPENING/CLOSING), effective dates and checklist revision. Examples: kitchen closer -> fryer condition and temperature reading, surface sanitation; dining-room opener -> arrange tables and place cutlery. Items define instruction/SOP link, due offset/window, type (CONFIRMATION, MEASUREMENT, EXCEPTION), required evidence, allowed value/unit and manager verification policy. Templates can be enabled, disabled or cloned per venue; edits apply to future assignments only.

### Assignment rules
The main HORECA scheduling service is the authority for planned shifts; HORECA Time remains authoritative only for attendance and does **not** own tasks. When a rostered shift is published/changed, the task service deterministically matches template version to venue, station, role and shift kind, then creates a `shift_checklist_instance` and per-item `task_assignments` tied to employee_id and shift_id. Idempotency key includes shift_id, template_revision and item_id. No duplicates on event replay. A published roster change triggers explicit reassignment/cancellation with audit trail; completed records remain attributable to the original actor. No automatic reassignment based solely on clock-in/out.

If a station has multiple qualifying staff, a manager-configured assignment policy determines a named owner, e.g. shift lead, named station assignment or explicit manager selection; never silently assign every task to everyone. Manager can delegate with reason and auditable event. A task is visible only to authorized employee(s) and venue managers.

### Lifecycle and evidence
PENDING -> IN_PROGRESS -> SUBMITTED -> VERIFIED (when required); alternatives BLOCKED, OVERDUE, CANCELLED, REOPENED. A simple setup confirmation may go directly from SUBMITTED to COMPLETED when policy allows. Store assigned_to, completed_by, completed_at server timestamp, reviewer, review time, original template revision, shift, venue, evidence, reason and immutable audit events. Completed-by may differ from assigned-to, with an explicit takeover/delegation record.
For measured safety tasks, capture actual numeric reading, unit, method, threshold/policy version, timestamp and any corrective action. A confirmation checkbox is not proof of acceptable temperature; out-of-range measurements create an exception requiring authorized review. Fryer temperature threshold must be defined by the venue's documented procedure; do not hardcode example temperatures as compliance rules.
Managers see per-shift, per-station and per-employee completion, missed checks, exceptions and verification queue. Personal task screen displays only a short checklist at appropriate opening/closing times; do not interrupt active service except for safety-critical exceptions.

### Proposed task domain tables
`task_templates`, `task_template_items`, `shift_checklist_instances`, `task_assignments`, `task_submissions`, `task_measurements`, `task_reviews`, `task_exceptions`, `task_audit_events`, `task_outbox`. Foreign reference to shift and employee IDs with business/venue authorization; versioned snapshots avoid retroactive template changes. The task domain belongs to main HORECA, not the separate Time database.

### Suggested API contracts
GET /api/v1/staff/me/shift-tasks
POST /api/v1/staff/tasks/{id}/submit
GET /api/v1/manager/shift-tasks?shift_id=...
POST /api/v1/manager/tasks/{id}/reassign
POST /api/v1/manager/tasks/{id}/review
GET/POST/PUT /api/v1/manager/task-templates (versioned, scoped, RBAC)
All mutations enforce idempotency, scope, version checks and audit events.

### Validation and rollout
Test synthetic kitchen closing and dining-room opening shifts, assignment determinism, template versioning, schedule change/reassignment, missed tasks, duplicate events, cross-tenant denial, numeric measurement validation and exception review. Introduce during Nov 24–26 task taxonomy work; add roster-triggered assignments alongside Nov 27–Dec workforce work; pilot Feb–Mar 2027. Do not activate real staff data, external notifications, paid services or actual compliance certification.

## Equipment noncompliance and conditional technician escalation (v1.3 extension)
When a staff member reports equipment failing a configured check (e.g. fryer does not reach documented target temperature), create an immutable, venue-scoped compliance/maintenance incident linked to the shift task, equipment asset, reporter, actual measurement, policy/SOP revision, timestamps and any immediate safety action. Reporting must be possible even if no checklist is due.

**Routing invariant:** notify the authorized shift/venue manager in all cases. If and only if an active, authorized technician assignment exists for that business/venue and equipment category, also create an in-app technician alert and technician work item. If no eligible technician exists, only the manager gets the initial notification and retains responsibility for external maintenance arrangements. Manager notification never depends on technician acknowledgement. An unassigned or inactive technician must not receive confidential venue alerts.

**Urgency and safety:** rules derive initial severity (NORMAL/HIGH/CRITICAL) from configured SOP/equipment criteria, with staff able to flag a suspected hazard. Technician may raise severity and mark urgent; authorized managers can also raise it. Safety-critical minimum severity cannot be downgraded without documented authorized review. For equipment with a suspected safety risk, display a clear out-of-service/hold instruction pending competent assessment; software must not claim physical isolation occurred unless a person records that action. No universal fryer temperature threshold is assumed.

**Lifecycle:** REPORTED -> ACKNOWLEDGED -> TRIAGED -> IN_REPAIR -> READY_FOR_RETEST -> VERIFIED -> CLOSED; alternate BLOCKED, REOPENED. Technician acknowledgement, manager acknowledgement, repair and return-to-service approval are separate events. A technician cannot unilaterally mark equipment safe for use unless explicitly authorized by policy. Retest and approved release are required when the equipment has been placed out of service. All transitions are RBAC- and venue-checked, timestamped and auditable.

**Notification behavior:** persistent in-app manager alert always; conditional in-app technician alert only when assigned. Deduplicate by incident_id and recipient. Track delivered/read/acknowledged separately. Escalate unacknowledged urgent incidents to authorized backup manager(s) using configurable local thresholds. Never automatically contact external services, SMS, email or push in prototype phase. If technician availability changes after creation, manager can explicitly reassign, with audit trail.

**Proposed entities:** equipment_assets, equipment_technician_assignments, compliance_incidents, incident_measurements, incident_actions, incident_assignments, incident_notifications, incident_reviews, incident_audit_events, incident_outbox. All scoped to tenant/venue. No real employee, technician or customer data in fixtures.

**Suggested endpoints:** POST /api/v1/staff/incidents; GET /api/v1/manager/incidents; POST /api/v1/manager/incidents/{id}/acknowledge; GET /api/v1/technician/incidents; POST /api/v1/technician/incidents/{id}/triage; POST /api/v1/incidents/{id}/actions; POST /api/v1/incidents/{id}/verify; POST /api/v1/incidents/{id}/close. Require idempotency, version checks, permission gates and auditable actions.

**Tests:** with technician configured -> manager and technician alerted; without technician -> manager only; inactive/cross-venue technician excluded; urgency can be raised but critical cannot silently be downgraded; duplicate report and notification events deduplicated; unacknowledged urgent incident escalates; repair does not auto-close or auto-release equipment; only authorized verifier can close; no paid service or external notifications.

**Roadmap:** include incident routing contracts in Nov 24–26 task work; add synthetic incident and manager/technician views during Feb–Mar 2027 checklist/exception pilot, without displacing menu-first or workforce milestones.
