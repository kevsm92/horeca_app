# Floor-plan cross-tab drag invalidation — 2026-11-13 20:00 Europe/Brussels

**Scope:** In the offline editor, cancel an in-progress pointer drag when another tab updates the same venue layout. The storage handler now removes the pointermove listener and clears the gesture before loading the other tab's revision. Pointer cancel only restores its original position if the revision is still the one captured at pointerdown; pointerup likewise rejects stale gestures. A foreign pointercancel is ignored.

**Why:** Previously, a drag could be in progress while a storage event loaded a newer revision; the later pointercancel could restore old coordinates over the freshly loaded layout in memory.

**Tests:** `node --test tests/tables/floor-plan-cross-tab-drag.test.cjs` contains four source-contract regressions. These are structural checks, not a substitute for browser-level two-tab event tests. Test execution in this run was limited to in-process source assertions because GitHub content was accessible only through the connector; do not mark the Node suite or browser suite as executed.

**Next:** Browser-level two-tab storage/pointercancel/pointerup tests, plus audit of pointer capture cleanup. No live backend, deployment, payments or real data.
