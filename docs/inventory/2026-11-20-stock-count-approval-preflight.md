# 2026-11-20 21:00 Europe/Brussels — stock-count approval preflight

Distinct bounded increment after independent recount reconciliation: reject a stale ledger revision before a manager can begin a separate transactional stock-count approval.

- The pure offline preflight accepts only an independently consistent, unposted, uncertified recount for the requested venue and SKU.
- It checks the caller-provided trusted current ledger revision against the recount snapshot, rejects mismatches, and requires a manager ID in a trusted venue-specific grant set.
- Success returns **eligible_for_separate_transactional_review**, never an approval, physical attestation, stock adjustment, or legal certification.
- This is **not** a security boundary by itself: the caller must authenticate the manager, resolve venue-scoped grants and current revision from trusted storage in the **same write transaction**, recheck all invariants under locking, record immutable provenance, and require human sign-off. Do not use client-supplied grants or revisions.
- Synthetic identities and stock only. No public API, payment, supplier order, real staff/customer data, or external cost.
- Local verification: `python -m unittest -v test_stock_count_approval_preflight` (12/12 passed), `python -m py_compile stock_count_approval_preflight.py test_stock_count_approval_preflight.py` (passed).
- Next dependency: trusted SQLite recount event storage and transactionally enforced authorization/revision checks.
