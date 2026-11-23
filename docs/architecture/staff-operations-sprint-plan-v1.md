# HORECA staff operations implementation sprint plan v1.0

Status: APPROVED BACKLOG / NOT YET IMPLEMENTED
Date: 2026-11-23
Architecture: [Role-specific frontends, HORECA Time and equipment escalation](role-specific-frontends-and-horeca-time-v1.md)
Tracking: https://github.com/kevsm92/horeca_app/issues/3

## Guardrails and sequencing
- Implement on `develop` only; do not touch `main` without a separately authorized release process.
- Keep existing menu-first React/Python integration and scheduled hourly milestones first. Sprint windows are planning targets, not calendar automation changes.
- €0 additional spend. Synthetic venue/staff/technician data only. No production attendance, payroll, real email/SMS/push, Dimona integration, payments or external services.
- Each sprint closes only with reviewed implementation, tests, documentation and demonstrable synthetic acceptance; architecture documentation alone does not count as completion.
- The main HORECA application owns rosters, role workspaces, tasks, equipment incidents and technician assignments. Separate HORECA Time owns punches, breaks and attendance corrections; integrate through versioned APIs/events, never shared writes.

## Sprint 01 — Role permissions and contracts (Nov–Dec 2026)
**Dependencies:** inspect existing menu, table, React and Python contracts.
**Deliver:** /floor, /kitchen, /manager, /admin, /staff role shells and capability-based, tenant/venue-scoped backend access checks; task, shift and incident contract definitions. Preserve current menu flow.
**Tests:** forbidden role/venue routes and APIs rejected; no regression in existing menu/table tests.
**Done:** synthetic role matrix proves each shell sees only authorized navigation/data.

## Sprint 02 — Configurable checklist templates (Dec 2026)
**Dependencies:** Sprint 01.
**Deliver:** versioned, per-venue task templates by station, role and shift type (OPENING/CLOSING); manager CRUD, enabled status, due windows, evidence requirements, SOP link and item ordering. Sample kitchen closing and dining-room opening templates.
**Tests:** template revisions immutable for already generated shifts, unauthorized edits denied, venue isolation.
**Done:** fictional manager configures fryer check, table arrangement and cutlery setup without code changes.

## Sprint 03 — Roster-triggered assignment (Dec 2026–Jan 2027)
**Dependencies:** Sprint 02; stable roster contract.
**Deliver:** deterministic checklist instances per published shift and assigned employee, configurable named owner/shift lead selection for multi-person stations, idempotent schedule event handling, delegation and audit trail. Do not use attendance punches as assignment authority.
**Tests:** duplicates, shift cancellation/swap, reassignment, multiple staff, historical completion preserved.
**Done:** fictional kitchen closer and dining-room opener receive correct checklists once.

## Sprint 04 — Independent HORECA Time kiosk (Dec 2026–Jan 2027)
**Dependencies:** venue/employee reference contract, but not task execution.
**Deliver:** separate Python modular monolith, SQLite DB, kiosk-only React entry point, venue-bound device provisioning, employee PIN/badge mock, clock-in/out and break transitions, append-only attendance, corrections and manager review; versioned outbox and stale-aware manager projection.
**Tests:** duplicate punches, invalid transitions, PIN rate limit, revoked device, cross-venue denial, kiosk inactivity reset, offline fail-closed, correction audit.
**Done:** synthetic employee completes valid punch/break sequence at shared kiosk; no mobile punch UI/API flow.

## Sprint 05 — Staff checklist execution (Feb 2027)
**Dependencies:** Sprints 02–03.
**Deliver:** role-contextual opening/closing task view, one-tap confirmations, numeric measurements with units and documented thresholds, server timestamps, audit events, missed-task status and manager review.
**Tests:** nonnumeric readings, out-of-range readings, double submission, staff not assigned, SOP revision, unauthorized verification.
**Done:** fictional kitchen staff records fryer reading; table setup and cutlery confirmed; manager can identify assigned and completing staff.

## Sprint 06 — Equipment incident routing and technician escalation (Feb–Mar 2027)
**Dependencies:** Sprint 05 or independent incident reporting contract.
**Deliver:** generic equipment registry; staff fault reporting independent of checklist; incident state machine, safety hold, initial severity, manager-always in-app notification, technician notification only if active eligible venue technician exists, acknowledgement, repair, retest and authorized return to service.
**Tests:** technician/no technician branches; inactive/cross-venue technician excluded; manager always notified; idempotent alerts; urgency cannot silently downgrade; repair cannot auto-close.
**Done:** synthetic fryer failure appears in manager view and optional technician view with separate acknowledgements; no external messaging.

## Sprint 07 — Manager and technician workspaces (Mar–Apr 2027)
**Dependencies:** Sprints 03, 05–06, and Time read model where available.
**Deliver:** manager shift/task completion overview by person and station, overdue checks, incident severity/age, technician triage and repair log, backup-manager escalation, verification queue; show attendance projection freshness.
**Tests:** cross-venue access, technician capability restrictions, unacknowledged escalation, stale attendance display, manager release permissions.
**Done:** manager can answer who checked the fryer, who prepared tables, what failed and who is handling it.

## Sprint 08 — End-to-end integration and usability gate (Apr–Jul 2027)
**Dependencies:** Sprints 01–07.
**Deliver:** synthetic end-to-end opening/closing shift demos; role-specific screens with tablet/mobile responsive layouts; performance and accessibility review; security/concurrency tests; operational handbook and deployment checklist. Maintain menu-first regressions.
**Tests:** full scenario from roster -> tasks -> noncompliance -> manager/technician -> repair -> retest -> approval; kiosk outage/stale projection; no external services.
**Done:** reproducible offline demo, passing tests, no high-severity open blockers, no live data or paid services.

## Definition of done for every sprint
- Code and focused automated tests on `develop`, reproducible locally.
- Venue/tenant and role authorization verified on the backend.
- Synthetic fixtures only, no real personnel data or external communications.
- Documentation of APIs, event versions, states and audit semantics.
- Failure modes tested: duplicate requests, stale updates, missing technician, outage.
- No change to `main` and no displacement of existing menu-first roadmap milestones.

## Explicit exclusions
- Real payroll/Dimona integration, legally compliant live time registration, real technician dispatch, SMS/email/push, personal-device punching, new paid services, customer loyalty scope (separate issue #2).
- Actual production deployment requires separate authorization and Belgian labor/privacy/legal review.

## Next executable milestone
Inspect current `develop` route/API organization and add Sprint 01 role-capability matrix and task/incident JSON contract tests without changing existing user-facing menu behavior.
