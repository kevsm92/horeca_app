# HORECA SOP evidence lifecycle — v0.1 (2026-11-24)

Status: **architecture proposal, not implemented or legally validated**. Scope: one venue-scoped inspection/check lifecycle. This is not an inspector certificate or evidence of physical conformity.

## Trust boundaries and invariants

- Every record carries a server-derived `venue_id`; authenticated actors have venue-scoped permissions. Never accept a client-provided venue identifier as authorization.
- SOP documents are immutable per `(venue_id, sop_id, revision)`. Acknowledgement of a revision does **not** constitute a physical check, measured result, or manager verification.
- A check execution is an append-only event stream, not an editable checkbox. Events include `event_id`, `check_id`, `venue_id`, `actor_id`, `occurred_at_utc`, `recorded_at_utc`, `timezone_id`, `sop_revision`, `event_type`, `payload`, `previous_event_hash` and `event_hash`. Server records both timestamps; backdated events must be explicit corrections with reason, never overwrite original events.
- Check types: `observation` (physical check performed), `measurement` (observed numeric value + unit + instrument/equipment), `not_performed` (reason), `exception_opened`, `corrective_action_recorded`, `recheck_recorded`, `manager_verified`, `closed`, `correction_appended`.
- Outcome is separately `pass`, `fail`, `indeterminate`, or `not_performed`. A missing value/evidence cannot default to `pass`. No universal temperature or frequency thresholds; resolve venue-approved SOP revision and product/equipment rules.
- A failed/indeterminate/not-performed observation cannot be transformed into pass. A new recheck creates a distinct event with its own observed value and proof. Manager verification references the exact recheck and corrective-action event IDs; manager cannot silently edit them.
- Evidence attachment metadata records digest, media type, byte count, retention classification and authorized storage reference. No public URLs or embedded employee HR/health data. Hash chaining detects modification but is not proof that a real-world measurement was truthful.
- Minimum RBAC: `staff` may submit own factual observations and corrective actions; `manager` may verify a check but not rewrite it; `auditor` may view explicitly authorized, venue/period-filtered evidence only. A manager's own check requires a separate reviewer where segregation-of-duties is configured.
- Compliance dashboards show **internal operational status**, never certified legal compliance.

## State transition contract

| Current | Event | Next | Required condition |
| --- | --- | --- | --- |
| scheduled | observation/measurement | awaiting_review | actual observation, actor, SOP revision, recorded time and required evidence |
| scheduled | not_performed | exception_open | reason and responsible owner |
| awaiting_review | exception_opened | exception_open | failed/indeterminate observation or documented deviation |
| awaiting_review | manager_verified | closed | passing evidence, authorized manager, provenance reference |
| exception_open | corrective_action_recorded | awaiting_recheck | action, actor, owner and timestamps |
| awaiting_recheck | recheck_recorded | awaiting_review | new independent observation with evidence |
| awaiting_review | exception_opened | exception_open | failed recheck or unresolved issue |
| awaiting_review | manager_verified | closed | passing recheck and complete linked action chain |
| any | correction_appended | unchanged | reason, original event ID, new event; never mutate history |

No transition from `exception_open` or `awaiting_recheck` directly to `closed`. `not_performed` is never equivalent to a passing check. A manager can reject verification by recording a new exception.

## Persistence and concurrency

Proposed SQLite tables: `sop_revision`, `check_schedule`, `check_event`, `check_attachment`, `check_assignment`. All foreign keys include `venue_id`; unique `(venue_id, event_id)`, `(venue_id, check_id, event_sequence)`, and `(venue_id, sop_id, revision)`. Append event and advance projected check state in one `BEGIN IMMEDIATE` transaction, comparing expected event sequence. Reject stale writes as conflicts; retry only at command boundary. Enforce no update/delete on event history via database triggers and restricted write interfaces. Hash canonical serialized event plus prior hash; use a versioned canonicalization format.

## Acceptance tests for implementation

1. Staff acknowledgement of revision 3 does not create an observation or mark a scheduled check complete.
2. Missing measurement/unit/instrument for a measurement-type check is rejected.
3. A failed temperature observation opens an exception; corrective action, fresh passing recheck and distinct authorized manager verification are required before closure.
4. Missing check, not-performed check, failed recheck and unresolved exception cannot be marked passed/closed.
5. Cross-venue check IDs and foreign references return not-found/denied without revealing existence; unauthorized staff verification is denied.
6. Concurrent writes with the same expected sequence yield one success and one conflict; original evidence remains immutable.
7. Corrections append a reason and reference without changing original timestamps or values.
8. Export restricted to venue, period and authorized SOPs includes revision, UTC/local time context, corrective-action chain and integrity digest; excludes payroll, sickness and unrelated staff records.

## Camera application boundary

An edge camera may emit only a **provisional observation** with venue/device scope and coverage/confidence status. For an opened-perishable label, human-readable `OPENED ON` must be visibly read and reconciled with a trusted opening event and product rule; missing, unreadable, obscured, expired, unmatched or uncovered labels open manual-inspection tasks, never automatic passing checks. Do not collect real footage, identify employees or deploy camera devices in this phase.

## Dependencies and next increment

Implement the tables and append-only command handler against the actual verified Python SQLite architecture, then run the acceptance tests. This document intentionally does not assert current repository implementation, legal thresholds, hosting readiness or verified application tests. Validate applicable FAVV/AFSCA guide, GDPR/Belgian workplace camera requirements and local fire/HVAC authorities separately before operational use.
