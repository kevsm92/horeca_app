# HORECA menu API — authenticated read contract and integration audit v0.1

**Date:** 2026-11-21 (Europe/Brussels). **Scope:** design-only retry of the previous architecture deliverable; no application code change, public server, or live data.

## Verified develop implementation (2026-11-21)
GitHub develop head inspected: `f992aab4ac21e91be5b9a2b67e59cfc98473760d` before this document commit. This repository ALREADY has read-only Python WSGI HTTP adapters and venue-scoped SQLite menu catalog modules; it is incorrect to describe `GET /api/v1/menu-items` as entirely unimplemented.

- Root `menu_http.py` calls `menu_catalog.list_items` and emits `{ "items": [{ "id", "category", "name", "price_cents", "currency", "available", "description" }] }`; it accepts a host-injected trusted session resolver and returns 503 on catalog failure. Root `menu_wsgi.py` and `menu_catalog_store.py` are a second offline WSGI/catalog pair.
- `prototypes/menu/menu_app.py` composes `prototypes/menu/menu_http.py` and `prototypes/menu/menu_sessions.py`. The latter looks up digests of pre-provisioned opaque cookies, validates expiry/revocation and server-owned venue grants; this is not a deployed login/session issuance service.
- `frontend/src/menuClient.js` expects `item_id` and `kind`, not the root adapter's `id` and `category`. The prototype's menu response is a different contract from the root adapter. **Choose one canonical endpoint/storage path and reconcile this discrepancy with contract tests before asserting Python-to-React integration.**
- The repository contains synthetic Python catalog fixtures and React API adapter tests. Presence of these files does not establish a running authenticated browser-to-Python deployment or complete end-to-end test.

## Desired public contract, pending canonicalization
`GET /api/v1/menu-items?kind=food|drink`, `200 application/json`, response `{"items":[...]}`. The browser's currently validated shape is stable opaque `item_id`, `kind` (`food`|`drink`), `name`, integer `price_cents`, boolean `available`, and optional `description`. EUR is fixed in Python's root catalog but is not currently a required React response field. Optional allergens and safe image metadata are **future additions**, not verified current endpoint features. Any schema change needs matching Python and React tests, including strict value limits.

## Required security boundary
1. Resolve the authenticated principal exclusively from server-validated, nonexpired, nonrevoked session state. Do not create a demo user from a request header or query argument. Missing/invalid identity -> 401 and no data.
2. Derive the active venue exclusively from verified session membership; a client-provided `venue_id` can never select another venue. Missing venue grant or `menu:read` permission -> 403 without disclosing catalog records.
3. Query SQLite with a parameterized `WHERE venue_id = ?` and composite `(venue_id, item_id)` identity. Do not load other tenants and then filter in Python. Return only allowlisted fields: never recipe costs, supplier terms, session digests, staff or guest details.
4. Fail closed on database/session errors with generic JSON; current Python menu adapters use **503** for storage errors, not 500. Exclude SQL, filesystem paths, credentials and tracebacks from the response.
5. Preserve read-only GET behavior, `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, and method/path rejection. Analyze CORS, browser origin, secure/HttpOnly/SameSite cookies, session issuance, expiry, revocation, throttling, and CSRF for future writes before any live hosting. The offline WSGI factories are not safe deployment authorization by themselves.
6. Use fictional data only; no real transactions, guest/staff information, suppliers contacted, hardware, camera capture, billed services, or external deployment.

## Required acceptance tests before marking first E2E integration complete
- Missing, expired, revoked, duplicated or malformed cookies -> 401; no item payload.
- No menu permission or server-verified active venue -> 403; no item payload.
- Synthetic venue A sees A's food/drinks, never B's, even when item IDs overlap and a malicious header/query references B.
- Invalid category filter/query and non-GET methods have deterministic 400/405 responses; empty authorized venue yields `{"items":[]}`.
- SQLite or session-store failure is generic and does not reveal internals; no partial cross-venue data.
- Canonical Python response passes `frontend/src/menuClient.js` parser against the real synthetic SQLite fixture, preserving integer cents and food/drink type. Verify loading/error/empty/abort UI states.
- Test same-origin authenticated Python-to-React flow locally; retain dormant table API clients and existing table/seat safeguards.
- Run relevant Python and frontend regression suites on a checked-out exact develop revision; document any suites that could not run.

## Sequencing and evidence limits
This file is a **source-inspected technical specification**, not an implemented API change or passing integration test. Next task: choose canonical Python menu route (root or prototypes), align the server response to the existing React contract, add same-origin authenticated integration regression tests, and only then consider local UI wiring. No public backend until full authentication, authorization, CSRF/origin, tenant, secrets and hosting-cost gates pass.

The stable `main` branch was verified before this commit at `46115441ddb73212178a6d24f5e5cf832485b3e7` and must remain untouched.