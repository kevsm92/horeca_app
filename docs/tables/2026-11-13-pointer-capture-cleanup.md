# Pointer-capture lifecycle cleanup — 2026-11-13 (Europe/Brussels)

One bounded offline floor-plan reliability change. A shared cleanup function now removes pointermove, pointerup and pointercancel listeners and releases captured pointer IDs on pointerup, pointercancel, storage revision invalidation, and venue switching. A second pointerdown is ignored while a drag is active. Existing revision checks and rollback remain.

Source inspection checks: 8/8 passed using the GitHub-retrieved HTML and in-process assertions. The committed Node test file contains four structural regression cases; **Node and browser tests were not executed** in this connector-only run. Browser verification still needed: two-tab storage event during captured drag, release after cancel, and new drag following invalidation.

No backend, camera, payments, deployment, real data or external paid services. Cost €0.
