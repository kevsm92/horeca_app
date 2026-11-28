# 2026-11-20 20:00 Europe/Brussels — independent stock recount gate

One bounded, offline inventory-operations increment following the earlier variance review.

- A second, independently attributed count must match venue, SKU and snapshot revision.
- Recounts disagreeing beyond a caller-approved integer tolerance remain disputed.
- Even consistent recounts remain pending manager review; no physical conformity attestation, inventory adjustment or ledger write occurs.
- Synthetic actors and stock only. Callers must authenticate staff, enforce venue RBAC, establish the trustworthiness of physical counts, and persist append-only provenance before integration.
- No public service, paid service, camera capture, real supplier or customer operation.
- Run: `python -m unittest -v test_stock_count_recount_gate`.
- Next: trusted SQLite count event persistence and transactional manager approval with stale-revision recheck.
