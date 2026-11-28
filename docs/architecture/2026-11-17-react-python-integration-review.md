# React/Python integration audit — 17 November 2026

## Source reviewed

Starting develop HEAD: c51c976b7c2800cd49354af5d762c3c57b70803f. Stable main was 46115441ddb73212178a6d24f5e5cf832485b3e7.

The latest React sprint added pure client-side table/POS rules, a built-in Node.js unit-test script, and ten tests. That Node executable is a frontend development test runner, not an HTTP backend. Current React screens use synthetic, in-memory table, order, kitchen and reservation state. No Python API calls are present in frontend/src/main.jsx.

The tracked Python files include SQLite seating domain prototypes (tables_foundation.py, tables_guest_count.py, tables_capacity.py), but no verified authenticated Python HTTP application entry point or tables endpoint was found in the develop repository tree. Those domain prototypes explicitly leave caller authorization to an outer layer. Prior local ZIPs must not be treated as recovered or integrated code.

## Scoped addition

frontend/src/pythonApi.js is a DORMANT read-only browser API adapter, with injected-fetch tests in frontend/tests/pythonApi.test.js. It proposes a same-origin GET /api/v1/tables route and a JSON response shaped like:

    {"tables":[{"id":"T1","seats":4,"guests":2}]}

This is a proposed contract, NOT an existing route. The adapter does not make network calls until explicitly invoked, it cannot mutate tables, and it is deliberately not wired into the current demo because the authenticated Python API route is not yet available. It rejects non-JSON responses, invalid capacities, duplicate IDs, impossible occupancy, HTTP errors and network failure rather than showing unverified backend data. No Node.js app server, proxy, alternate database or public endpoint was created.

## Required Python service contract before UI integration

The real Python API must authenticate and authorize the active session, derive venue scope on the server (never trust a browser-supplied venue), and read physical table inventory and current seating sessions consistently. Its JSON list must represent authoritative capacities and occupancy. Future seating/order mutations must enforce venue RBAC, CSRF/session protection, concurrency, physical capacity and no double seating in Python/SQLite with negative and race-condition tests. A browser validation helper cannot enforce these rules on its own.

Only after this route is implemented, secured and tested should React replace its in-memory table data with backend reads and safely add write commands. Static React assets may be hosted by the verified Python app; Node is only a development/build/test tool. Any deployment still requires separate security and zero-cost review.

## Verification

The existing tableRules.js and tableRules.test.js Git blob SHAs matched the originals exactly when copied locally; their ten Node tests passed. The new adapter passed nine additional local unit tests using fake fetch; total: 19 passed, 0 failed, with Node 22.16.0. Syntax checks passed for the pure JavaScript modules. The complete React/Vite build, actual Python HTTP integration, and full-repository suite were NOT executed. No live deployment, real venue data, payment activity or additional spending was undertaken.

Target branch: develop only. Main remains the stable reviewed branch.
