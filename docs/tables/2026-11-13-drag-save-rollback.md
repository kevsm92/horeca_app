# 2026-11-13 19:00 — Drag-save failure rollback

The floor-plan editor previously rendered a dragged table at its new coordinates even when browser persistence failed. The pointer-up handler now restores the table's pre-drag coordinates if the save fails and the revision has not changed. If another tab has advanced the revision and save has refreshed state, it does **not** overwrite that newer state.

Scope: `endDrag` only; keyboard movement rollback was already covered. No server persistence or multi-user locking is implied. Test: `node --test tests/tables/reference-redesign-drag-rollback.test.cjs`. Uses synthetic coordinates and no external services.

Follow-up: test pointer-capture cancellation and revision conflict in full browser integration; ensure drag preview cannot leave a stale layout during concurrent storage changes. No deployment or spend.
