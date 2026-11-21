# 2026-11-11 — Tables foundation: physical inventory and seating invariants (architecture increment 01)

Status: **specification only**. The inspected `develop` README explicitly says historical application archives have not been recovered. No application schema or test suite was verified; this document must not be mistaken for an integrated implementation.

## Scope and trust boundary
A physical table belongs to exactly one venue. Its immutable identity is distinct from its editable label, floor-plan representation and seat count. The server, not a client-supplied venue ID, determines the authorized venue from an authenticated principal. Until venue RBAC and CSRF are tested, do not expose write routes publicly.

## Proposed PostgreSQL schema (not applied)
```sql
CREATE TABLE physical_tables (
  id uuid PRIMARY KEY,
  venue_id uuid NOT NULL REFERENCES venues(id),
  label text NOT NULL,
  physical_seats integer NOT NULL CHECK (physical_seats BETWEEN 1 AND 100),
  enabled boolean NOT NULL DEFAULT true,
  revision bigint NOT NULL DEFAULT 0,
  UNIQUE (venue_id, id),
  UNIQUE (venue_id, label)
);
CREATE TABLE seating_sessions (
  id uuid PRIMARY KEY,
  venue_id uuid NOT NULL,
  table_id uuid NOT NULL,
  guest_count integer NOT NULL CHECK (guest_count > 0),
  started_at timestamptz NOT NULL DEFAULT now(),
  ended_at timestamptz,
  revision bigint NOT NULL DEFAULT 0,
  FOREIGN KEY (venue_id, table_id) REFERENCES physical_tables(venue_id, id),
  CHECK (ended_at IS NULL OR ended_at >= started_at)
);
CREATE UNIQUE INDEX one_active_seating_per_table
  ON seating_sessions(venue_id, table_id) WHERE ended_at IS NULL;
```
All identifiers are server-issued; a foreign key for `venues` and actual database dialect must be checked against recovered source before migration. This prototype deliberately does not assume that a floor-plan shape equals a physical table or that visual width determines capacity.

## Atomic seat operation
1. Authenticate actor and authorize `tables:seat` in the venue; reject mismatched venue/table with a non-enumerating response.
2. Begin database transaction; lock the selected `physical_tables` row using `SELECT ... FOR UPDATE`.
3. Require enabled table, `1 <= guest_count <= physical_seats`; ensure no active session. Insert seating session with server timestamp. The partial unique index is the final concurrent double-seat guard; map its conflict to HTTP 409.
4. Commit; return session ID and revision. Never silently switch to another table. Client retry requires a scoped idempotency key with payload fingerprint and atomic storage; conflicting reuse must return 409.
5. End session with a conditional update, audit actor and timestamp. Never delete historical sessions.

## Capacity changes
Any seat-capacity reduction must lock the table row and reject values below the guest count of an active seating session. Disabling a table with active seating is rejected. Visual dimensions and position will be stored separately in later dated increments; they must not create seats.

## Acceptance cases for implementation
- A venue A actor cannot read/seat venue B's table, even by guessing its UUID.
- Guest count 0, negative, or above physical capacity is rejected.
- Two concurrent seat attempts for one table yield exactly one active session and one conflict.
- A second seat attempt after a properly ended session succeeds; prior history remains.
- A concurrent resize below active guest count is rejected, including races with seating.
- Disabled table cannot be seated; duplicate labels within venue are rejected, while different venues may reuse labels.
- A repeated idempotency key and identical payload returns the original result; altered payload conflicts.
- Database rollback leaves no partial seating record.

## Deferred dependencies
Recover and inspect real HORECA models/migrations, authentication and tests before implementing this schema; select DB-specific locking strategy. Add physical table CRUD, transactional service, race tests and a dated completion ledger. Do not claim a Tables tab or Seat button exists based on this spec.

Constraints: synthetic fixtures only; €0 incremental cost; no deployment, live integrations or real personal data.
