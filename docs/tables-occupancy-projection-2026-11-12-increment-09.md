# Tables occupancy projection: fail-closed read model (2026-11-12, increment 09)

Status: standalone architecture/test contract. The recovered HORECA application source is not present in the verified repository README; no UI or production persistence is claimed.

## Scope distinct from increment 08
Increment 08 specified navigation and seat commands. This increment defines the **read-side occupancy projection** feeding both a separate Tables tab and a future floor-plan/list view, including explicit data-integrity failure behavior.

### Projection inputs
- Authenticated venue context `venue_id`, obtained from the server-side principal, not from a query string.
- Physical tables: stable ID, venue ID, label, integer capacity >= 1, enabled flag.
- Seating sessions: stable ID, venue ID, physical table ID, positive integer guest count, active flag.
- Query must restrict *both* tables and sessions to the principal's venue before projection; a defense-in-depth validator must reject any cross-venue record if one leaks into the result set.

### Deterministic output
One row per physical table, sorted by stable table ID, exposing only `id`, `label`, `capacity`, `occupied_guests`, and `status`. Never expose reservation PII, staff identifiers or unrelated sessions.

- Exactly one active session: `occupied`, with its guest count, even if the table was subsequently disabled.
- No active session, enabled: `available`, occupied guests 0.
- No active session, disabled: `unavailable`, occupied guests 0.
- Inactive historical sessions never contribute to occupancy.

### Fail-closed invariants
Reject the entire projection (and log an internal sanitized integrity event) on duplicate physical IDs, duplicate active sessions, active sessions referencing missing tables, cross-venue tables or sessions, invalid capacity, or active guest counts outside 1..capacity. Do not render corrupt data as `available`; do not silently hide integrity errors. Do not treat this read model as the atomic write-side seating lock.

### Verification performed offline
A separate local Python reference prototype was executed with **13 passing unittest cases** on 2026-11-12: available; occupied; disabled empty; disabled occupied; inactive ignored; cross-venue table; cross-venue seating; double seating; orphan session; over capacity; boolean guest count; duplicate physical ID; deterministic ordering. The reference prototype is not integrated into the repository or its CI; these results are not application-level verification.

### Next dependency
Recover application source, implement the projection against authenticated venue-filtered database queries, add regression tests for the same invariants and compare floor-plan and list statuses. November 13 coordinate editing must not alter physical inventory or active seating.

No production data, deployment, payment activation, metered services or external communication is authorized by this document.
