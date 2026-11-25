# 2026-11-25 — Transactional outbox, bounded architecture increment (v1)

## Verified baseline and scope
The reachable `develop` README describes repository initialization and explicitly says historical sprint ZIPs are not integrated. No application domain schema or Python HTTP server was verified in this run. Therefore this is a standalone, **not integrated** design for a future SQLite/Python workflow-automation slice. Do not mistake it for deployed automation.

## Contract
- `outbox(id INTEGER PRIMARY KEY, venue_id TEXT NOT NULL, event_key TEXT NOT NULL, event_type TEXT NOT NULL, payload_json TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('pending','leased','done','dead')), attempts INTEGER NOT NULL DEFAULT 0, available_at TEXT NOT NULL, lease_token TEXT, lease_until TEXT, created_at TEXT NOT NULL, UNIQUE(venue_id,event_key))`.
- The producer inserts a domain change and its outbox row in **one SQLite transaction**. A repeated `(venue_id,event_key)` with identical event type/payload is a no-op; conflicting reuse is an error. Do not send network messages in the producer transaction.
- Worker uses `BEGIN IMMEDIATE`, selects one due pending event (or expired lease) for an **authorized, server-derived venue**, then writes a fresh unpredictable lease token, incremented attempts, and lease expiry before committing.
- Only the holder of the current `(venue_id,id,lease_token)` can mark done or reschedule. On transient failure set a bounded exponential backoff and retry; after configurable max attempts mark dead and require human review. Never silently drop a compliance exception.
- Consumers must be idempotent using `(venue_id,event_key)`; leasing is **at-least-once**, not exactly-once delivery. Mock task triggers only: `task.requested.v1`, `inspection.deviation.v1`. Do not treat an emitted event as proof that an inspection occurred or passed.
- Keep `event_type` allowlisted; validate schema version and payload size; never place secrets, guest identifiers, medical information, or staff pay in generic event payloads. Protect venue isolation and event/audit retention with explicit policy.
- UTC offset-aware timestamps only; no assumed legal temperature thresholds. No external queue, email, payment provider, webhook, camera, or production data.

## Acceptance checks before integration
1. Duplicate same-key enqueue yields one row; conflicting content fails.
2. Rolling back the domain transaction rolls back the event.
3. Venue B cannot claim or acknowledge venue A's event.
4. Concurrent workers cannot claim the same unexpired lease; expired lease is reclaimable.
5. A stale lease token cannot acknowledge a reclaimed event.
6. Retry exhaustion goes to visible dead-letter review; recovery is audited.
7. Mock task consumer deduplicates replays and does not mark an SOP check complete.

## Integration dependencies and next increment
Recover and verify the actual latest Python domain schema and auth/venue model; choose existing migration conventions. Implement the outbox table and producer in the same connection/transaction as a fictional task creation, then add focused SQLite concurrency and tenant tests. Keep `main` unchanged and deployment disabled until backend security and free-hosting gates are verified.

## Verification boundary
A separate local Python SQLite reference exercise in this run passed four unittest cases (idempotency, tenant isolation/ack, retry/stale lease, rollback); it is **not** the repository implementation and does not establish concurrency safety. This document itself is the only intended GitHub deliverable for this milestone.
