# ADR-2026-11-25-01: SQLite transactional outbox for offline task triggers

Status: **proposed, not implemented**. Scope: one bounded workflow-automation architecture increment. Date: 2026-11-25 (Europe/Brussels).

## Verified baseline and constraints
The reachable `develop` README and initial commit contain repository/branch guidance, not a recoverable Python service, SQLite schema or tests. Do **not** infer historical sprint archives are integrated. This ADR specifies the next implementation contract without claiming executable integration. All example data is fictional; no live notifications, external integrations, payments or deployment.

## Atomic persistence contract
An authenticated, venue-authorized domain command must write its business mutation and an outbox row in the **same SQLite transaction**. Use `BEGIN IMMEDIATE` where writer serialization is necessary. A successful commit means both are durable; rollback means neither exists. Do not publish before commit. The outbox is an internal work queue, not a public event stream.

Proposed `outbox_events` schema (migration required once the actual database is recovered):

```sql
CREATE TABLE outbox_events (
  id TEXT PRIMARY KEY,
  venue_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  aggregate_type TEXT NOT NULL,
  aggregate_id TEXT NOT NULL,
  event_version INTEGER NOT NULL CHECK (event_version > 0),
  payload_json TEXT NOT NULL,
  occurred_at_utc TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'pending'
    CHECK (state IN ('pending','leased','delivered','dead')),
  attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  available_at_utc TEXT NOT NULL,
  lease_token TEXT,
  lease_expires_at_utc TEXT,
  delivered_at_utc TEXT,
  last_error_code TEXT,
  UNIQUE (venue_id, event_type, aggregate_type, aggregate_id, event_version)
);
CREATE INDEX outbox_due_idx
  ON outbox_events(state, available_at_utc);
CREATE TABLE task_trigger_receipts (
  venue_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  trigger_key TEXT NOT NULL,
  task_id TEXT NOT NULL,
  PRIMARY KEY (venue_id, event_id, trigger_key)
);
```

## Single offline trigger: failed SOP check -> manager review task
Input event `sop.check.failed.v1` contains only `check_id`, `sop_revision_id`, `station_id`, `occurred_at_utc`; no employee health, photos or raw measurements in the event payload. The authoritative check/evidence remains in venue-scoped storage. The handler looks up the check under the event's venue, verifies it is still failed, and creates a manager-review task referencing the check, with `task_trigger_receipts` inserted in the **same transaction** as the task. It must never mark a check passed, auto-close a deviation or assert regulatory compliance.

## Dispatcher and failure semantics
1. A local worker leases a due pending event by atomically changing state to `leased`, assigning a random lease token and expiry, incrementing attempts; claim only one row per transaction. Expired leases may be reclaimed.
2. The handler executes venue-scoped task creation and its receipt atomically. Repeated delivery sees the receipt and returns success without creating another task.
3. Mark delivered only when the matching lease token is held. If the worker crashes after task commit but before acknowledgement, redelivery is safe because the receipt is unique.
4. Retry transient errors with bounded exponential backoff and jitter; classify invalid schema, unknown event version and exhausted attempts as `dead` for human investigation. Never silently drop an event or run an unrecognized handler.
5. Use UTC instants for queue ordering and record venue timezone separately for presentation. No remote network calls in this prototype.

## Trust boundaries
Venue ID is derived from the authenticated server-side command context, **never** from an untrusted event/request body. The worker must validate event type, version, payload schema and venue-scoped references before acting. Only a privileged internal dispatcher can lease/acknowledge. Do not expose outbox payloads or staff-sensitive task details to guest sessions. No external broker or paid service.

## Focused acceptance tests for the eventual implementation
- Transaction rollback leaves neither domain mutation nor event; success leaves exactly one of each.
- Duplicate domain command/event version cannot create duplicate outbox events.
- Two workers racing for one due event result in one valid lease.
- Crash after task commit and before acknowledgement yields exactly one task on retry.
- Cross-venue check reference is rejected without creating a task or receipt.
- Unknown event version is quarantined; transient failure retries and terminal failure remains inspectable.
- A failed or missing check never becomes a passed check through this automation.

## Dependency / next slice
Recover or implement the authenticated Python SQLite domain baseline and migrations, then implement **only** the atomic event insert + rollback test before adding the dispatcher. Coordinate with the food/drink menu API priority and preserve the independent frontend schedule. This ADR does not authorize a public backend, customer communications or any deployment.
