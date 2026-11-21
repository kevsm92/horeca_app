# Supplier directory v0.1 — venue-scoped offline contract

Status: **architecture-only**, 2026-11-21 (Europe/Brussels). No implementation, migration, or tests are claimed. This document is a bounded supplier-directory milestone, not authorization to contact suppliers.

## Scope and trust boundaries

Maintain fictional suppliers and per-venue supplier product mappings for purchasing drafts. Supplier identity is not automatically shared across venues. Never send orders, messages, invoices or payment requests; no real supplier contact data. The API, if implemented later, must derive `venue_id` from an authenticated, authorized server-side session, never from a query parameter, request body, or client-supplied header. Supplier SKU mappings are **not** menu items: future food/drink menu API reads remain a separate priority.

## Proposed SQLite schema (migration proposal; not executed)

```sql
PRAGMA foreign_keys = ON;
CREATE TABLE supplier (
  venue_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL,
  display_name TEXT NOT NULL CHECK(length(trim(display_name)) BETWEEN 1 AND 160),
  status TEXT NOT NULL CHECK(status IN ('active','inactive')),
  created_at TEXT NOT NULL,
  PRIMARY KEY (venue_id, supplier_id)
);
CREATE TABLE supplier_sku (
  venue_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL,
  sku_id TEXT NOT NULL,
  supplier_product_code TEXT NOT NULL,
  product_name TEXT NOT NULL CHECK(length(trim(product_name)) BETWEEN 1 AND 200),
  purchase_unit TEXT NOT NULL CHECK(purchase_unit IN ('each','kg','g','l','ml')),
  pack_quantity_milli INTEGER NOT NULL CHECK(pack_quantity_milli > 0),
  unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0),
  currency TEXT NOT NULL DEFAULT 'EUR' CHECK(currency = 'EUR'),
  lead_time_days INTEGER CHECK(lead_time_days BETWEEN 0 AND 365),
  effective_from TEXT NOT NULL,
  effective_until TEXT,
  PRIMARY KEY (venue_id, supplier_id, sku_id),
  FOREIGN KEY (venue_id, supplier_id) REFERENCES supplier(venue_id, supplier_id),
  CHECK(effective_until IS NULL OR effective_until >= effective_from)
);
CREATE UNIQUE INDEX supplier_sku_code_unique
 ON supplier_sku(venue_id, supplier_id, supplier_product_code, effective_from);
```

`pack_quantity_milli` stores 1/1000 of the declared purchase unit (e.g. 1500 = 1.5 kg when `purchase_unit='kg'`); conversion to ingredient inventory base units requires an explicit approved mapping and must not be guessed. Monetary values use integer EUR cents. Supplier prices are snapshots with effective dates; historical draft purchase orders must preserve their quoted price and never be silently repriced.

## Required service invariants

1. Every read, update, deactivate, SKU lookup and join includes server-resolved `venue_id`. Cross-venue IDs return indistinguishable not-found responses; never leak supplier names.
2. Creating an SKU requires a supplier belonging to the same venue. Duplicate supplier code/effective-date combinations fail atomically; no partial writes.
3. Deactivation retains historical records and prevents new draft selection. Never delete referenced supplier identities or mutate past approved price snapshots.
4. Date ranges must not overlap for the same supplier product code in a venue; enforce in a single `BEGIN IMMEDIATE` transaction when creating or editing price versions (the index alone does not enforce interval overlap).
5. No network integrations, automatic procurement, supplier notifications or live invoice submission. No personal contact fields in this first slice.
6. Supplier directory access requires explicit venue-level procurement permissions; staff menu-browsing permission does not imply procurement access.

## Synthetic acceptance tests for the future implementation

| Test | Expected |
| --- | --- |
| Create supplier and two SKUs in venue A | Both persist and list only for A |
| Attempt to read A supplier with B session | Not found; no supplier metadata leaked |
| Create B SKU referencing A supplier | Rejected; no orphan row |
| Duplicate code/effective date | Unique conflict; unchanged row count |
| Overlapping effective intervals | Rejected transactionally |
| Negative price, zero pack quantity, invalid unit | Constraint failure |
| Deactivate supplier, then select for new PO draft | Selection denied; historic references remain |
| Concurrent conflicting price inserts | Exactly one succeeds |
| Unauthenticated / insufficient role | 401 / 403 without data |
| Synthetic-only scan | No real contacts, credentials, endpoints or outbound effects |

## Dependency and next step

Before implementing, inspect actual `develop` source and migrations; adapt naming to verified conventions. First recover/verify the Python authenticated menu catalog endpoint and React menu integration required by the 2026-11-17 directive; do not build an unauthenticated public API to expedite supplier work. Then implement this supplier schema and tests against the actual repository architecture. No deployment until all security and no-cost gates are verified.
