# Workflow outbox v1 — offline contract (2026-11-25)

**Status:** architecture-only; not an implemented event bus. **Scope:** one venue-scoped, SQLite transactional-outbox slice for mock operational task triggers. No network dispatch, staff messages, supplier orders or payments.

## Source verification and dependency gate

The reachable `develop` README states that historic archives have not been recovered. The Python application, migrations, authenticated venue context and task engine have **not** been inspected sufficiently to claim integration. Do not install this schema blindly or publish an HTTP endpoint. First locate and verify the actual SQLite transaction boundaries, task tables and migration conventions; adapt names to those verified interfaces.

## Durable contract

A domain mutation and its outbox insert MUST commit in **one SQLite transaction**. A caller must derive `venue_id` from authenticated server-side context, never an event payload or request header. The producer assigns an immutable UUID `event_id`, a unique `(venue_id, event_type, aggregate_id, aggregate_revision)` tuple and a fixed versioned schema. JSON payloads must contain only synthetic operational identifiers and non-sensitive task metadata; no health, wage, payment, customer, camera image or worker-surveillance fields.

Proposed migration (adjust to existing schema after source inspection):

```sql
CREATE TABLE workflow_outbox (
  event_id TEXT PRIMARY KEY,
  venue_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_version INTEGER NOT NULL CHECK (event_version >= 1),
  aggregate_id TEXT NOT NULL,
  aggregate_revision INTEGER NOT NULL CHECK (aggregate_revision >= 1),
  payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
  created_at_utc TEXT NOT NULL,
  available_at_utc TEXT NOT NULL,
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  state TEXT NOT NULL DEFAULT 'pending'
    CHECK (state IN ('pending','leased','delivered','dead_letter')),
  lease_token TEXT,
  lease_expires_at_utc TEXT,
  last_error_code TEXT,
  UNIQUE (venue_id,event_type,aggregate_id,aggregate_revision)
);
CREATE INDEX workflow_outbox_due
  ON workflow_outbox(state,available_at_utc,created_at_utc);
CREATE TABLE workflow_consumptions (
  venue_id TEXT NOT NULL,
  consumer_name TEXT NOT NULL,
  event_id TEXT NOT NULL,
  processed_at_utc TEXT NOT NULL,
  PRIMARY KEY (venue_id,consumer_name,event_id)
);
```

All timestamps are RFC 3339 UTC with explicit offset, normalized on input. SQLite foreign keys, WAL settings and busy timeouts must follow the verified app configuration. Do not put secrets or raw exception traces into `last_error_code`.

## Local-only dispatch semantics

1. In one `BEGIN IMMEDIATE` transaction, select an eligible pending event or an expired lease, set a random lease token, increment attempts and set lease expiry; commit before invoking the mock handler. A lease claimant must filter by server-authorized venue.
2. Mock handler `create_operational_task_v1` validates event type/version and venue ownership. In one transaction, insert `workflow_consumptions` first and create a task only if that insertion succeeds. Duplicate consumption is a successful no-op; task identity should also be deterministically tied to `event_id`.
3. Mark delivered only with matching `event_id + lease_token + venue_id`; a stale worker cannot acknowledge a newer lease. If the handler fails, return to pending with bounded exponential backoff and jitter; after a configurable maximum, mark `dead_letter` for authorized manual review, never silently discard.
4. Delivery is **at least once**, not exactly once. Consumer idempotency, not the queue, prevents duplicate tasks. Ordering is not globally guaranteed; consumers must reject or reconcile stale aggregate revisions.
5. Disable all external transports by default. No SMTP, webhook, payment processor, supplier submission, customer notification or production scheduling in v1.

## Initial synthetic trigger

`operational.check_due.v1` may request a task for a fictional refrigeration check with `{ "check_id": "synthetic-check-001", "sop_revision_id": "synthetic-sop-r1" }`. This event means **a check is due**, not that it was performed or passed. Actual measured checks, deviations, corrective actions and supervisor verification remain separate auditable records; no event may automatically certify compliance.

## Minimal acceptance gates before implementation merge

- Roll back a simulated domain write: outbox row must also roll back; successful write creates exactly one event.
- Concurrent/retried producer calls with the same aggregate revision yield one event; different venues remain isolated.
- Crash after mock task creation but before delivery acknowledgement: retry creates no duplicate task.
- Expired lease can be reclaimed; stale lease token cannot acknowledge it.
- Invalid version, malformed payload, unauthorized venue and dead-letter exhaustion fail safely.
- Tests use synthetic SQLite fixtures, with no outbound calls; report actual command and count. Until these tests run against verified source, this document is a **design proposal**, not a tested implementation.

## Next dependency

Recover/inspect current Python backend, SQLite migrations, task engine and authentication/authorization contracts; then implement the transaction-coupled producer as the next distinct milestone. Keep React food/drink menu integration as the separately prioritized cross-cutting API dependency.
