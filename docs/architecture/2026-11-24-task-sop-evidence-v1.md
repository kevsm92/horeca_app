# 2026-11-24 — Operational task and SOP evidence boundary (offline design v1)

Scope: venue-scoped tasks, priority, assignee, due date and append-only evidence. This is a design contract, not a deployed feature or an official compliance certificate.

## Minimum persistence contract

- `tasks`: composite primary key `(venue_id, task_id)`; title, assigned_staff_id, priority (low/normal/high), due_at (offset-aware), status (open/completed), created_at.
- `sop_revisions`: composite key `(venue_id, sop_id, revision)`; author, approver, applicability (station/role/equipment), effective_at, review_due_at, content digest. Never rewrite approved revisions.
- `task_events`: monotonic event ID, venue_id, task_id, actor, server-generated UTC timestamp, event_type, SOP revision reference, outcome, optional measured value/unit/instrument, evidence reference. Foreign keys include venue_id. Updates/deletes forbidden.
- Distinct event types: `sop_acknowledged` (read a specific revision), `physical_check_recorded` (pass/fail/not_performed), `manager_verified` (separate reviewer), `corrective_action_opened`, `recheck_recorded`, `exception_closed`.
- An acknowledgement or manager verification alone is never proof of a physical check. A failed/not-performed check remains a deviation; never mutate it into a pass. Rechecks append new evidence while retaining the original.
- Completion requires a passing applicable physical check and resolution of outstanding deviations; require manager verification when the venue SOP says so. Use one database transaction and compare-and-swap revision to avoid races.
- Derive venue and permissions from authenticated server-side session, never a client-supplied venue field. Restrict HR/private data from compliance exports.

## Initial safe slice

Implement a SQLite domain service and synthetic fixtures before any HTTP exposure. Required focused tests: tenant cross-reference denied, duplicate completion conflict, immutable event update/delete denied, acknowledgement-only cannot complete, failed check cannot complete, passing recheck retains failure history, unauthorized manager verification denied. All timestamps must be server-generated; no backdating or bulk fabricated sign-off.

## Camera interface dependency

A separate optional edge app can later submit device-scoped observations for an in-scope opened product. Human-readable **OPENED ON** date/time must be compared with trusted opening event and lot; missing/occluded/unreadable/untrusted labels create manual-review tasks, not automatic passes. Device events cannot independently certify food safety. No footage or hardware is enabled here.

## Boundaries and next work

Offline only, fictional records only, €0 additional spend. No real staff/guest data, supplier communication, payment activation, public API or deployment. Next increment: implement and test the SQLite task/evidence domain against the latest verified source, then add revisioned SOP persistence and explicit manager authorization. This document does not claim implementation or test execution in the GitHub repository.
