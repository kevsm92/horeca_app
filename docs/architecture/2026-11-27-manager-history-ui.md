# Manager history presentation contract (frontend only)

The Dashboard range selector (day/week/month) is presentation-only. Until an authenticated, versioned Python HTTP/JSON endpoint is verified, the UI shows an explicit unavailable state and a text-equivalent table with no invented values. A selectable period must never be interpreted as a successful fetch.

Future Python-owned contract proposal, **not implemented**: GET /api/v1/manager/metrics/history?range=day|week|month, scoped to the authenticated venue and role, with response schema version, venue timezone, currency, period boundaries, server-generated timestamp, per-series unit and points, and explicit unavailable/forbidden states. The Python owner must define and verify the final route, RBAC, tenant isolation, and response shape before frontend wiring. Never equate order value with captured revenue or scheduled work with actual attendance.

React remains a static client-rendered SPA. No Node runtime server, backend, database, credentials or polling introduced.
