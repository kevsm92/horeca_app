# Local-only Python menu bootstrap: security and React handoff (2026-11-17)

Status: **implementation contract only**, not a running service, deployment, or completed React integration.

## Verified repository baseline

At inspection, `develop` contained `prototypes/menu/menu_catalog.py`, `menu_sessions.py`, `menu_http.py`, `menu_app.py` and `test_menu_app.py`. The application factory accepts an already-open SQLite connection, and the tests use an injected clock and fictional session fixtures. It has no trusted runtime bootstrap, login endpoint, or browser integration. The frontend remains a separately edited workstream; avoid replacing its components without re-reading current HEAD.

## Next bounded implementation: loopback-only bootstrap

1. Add `prototypes/menu/local_bootstrap.py` with an explicit CLI entry point, **no import-time listener**, and a default refusal to bind any host other than `127.0.0.1`. No `0.0.0.0`, reverse proxy, or public hosting.
2. Require a caller-provided absolute SQLite path; refuse a missing/uninitialized schema and do not auto-create production-looking sessions. Open the database using a documented single-threaded WSGI lifecycle. Do not provision authentication tokens on HTTP requests.
3. Compose `make_authenticated_menu_app(db)` with `wsgiref.simple_server` only for local manual tests. Make shutdown close the DB. The browser must not be told that a synthetic session is a real login.
4. Keep the current API read-only; return no session secrets or customer data. Fail closed for invalid/expired/revoked cookies. Review duplicate `horeca_session` cookie ambiguity and disallow multiple values before using a browser.
5. A cross-origin React dev server cannot use this endpoint merely by setting `credentials: 'include'`. Do not enable wildcard CORS, invent session issuance, or weaken SameSite/CSRF controls to make the demo work. Prefer a narrowly configured same-origin local dev proxy after authenticated login/session issuance is independently tested.
6. Do not create a real login route or deploy this WSGI development server. Production deployment requires separate hardened server, HTTPS, session-cookie issuance, CSRF/origin policy, RBAC, tenant isolation, throttling, secret handling, and negative tests.

## Acceptance tests for the next implementation

- Importing the module opens no socket and does not create a database.
- A non-loopback bind address is rejected before socket creation.
- Missing/uninitialized database fails closed without creating a test identity.
- With an initialized temporary SQLite database and synthetic fixtures, a valid pre-provisioned cookie returns only its venue's food/drink items; absent, expired, revoked, malformed and duplicate cookies are rejected.
- A request with a caller-selected `venue_id` fails; `POST` fails with 405; invalid `kind` fails with 400.
- A local HTTP smoke test starts and shuts down deterministically, with no external network, live customer data or payment calls.
- Run the complete `prototypes/menu/test_menu_*.py` suite against the **exact fetched develop revision**, not a reconstructed subset, and record command/output.

## React handoff contract

Read `GET /api/v1/menu-items?kind=food|drink`; response `{ "items": [...] }` with stable IDs, kind, name, `price_cents`, availability and optional descriptions. The frontend must show loading, empty, 401/403 and retryable server-failure states, preserve prices as integer cents and avoid hardcoded fallbacks silently masquerading as live data. First wire Food & Menu, then POS browsing. The data remains **synthetic SQLite seed data**, not restaurant production API data.

## Guardrails

No new spend, public backend, activated payments, supplier orders, customer messages, real venue/staff data, hardware or camera footage. The separately scheduled React UI work continues. This document changes no runtime behavior.
