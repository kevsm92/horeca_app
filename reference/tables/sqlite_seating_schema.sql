-- HORECA offline seating reference schema, SQLite; no public API.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS physical_tables (
 venue_id TEXT NOT NULL, table_id TEXT NOT NULL,
 capacity_seats INTEGER NOT NULL CHECK(capacity_seats >= 1),
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
 PRIMARY KEY(venue_id, table_id)
);
CREATE TABLE IF NOT EXISTS seating_sessions (
 venue_id TEXT NOT NULL, session_id TEXT NOT NULL, table_id TEXT NOT NULL,
 guest_count INTEGER NOT NULL CHECK(guest_count >= 1),
 state TEXT NOT NULL CHECK(state IN ('active','closed')),
 PRIMARY KEY(venue_id, session_id),
 FOREIGN KEY(venue_id,table_id) REFERENCES physical_tables(venue_id,table_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_session_per_table
 ON seating_sessions(venue_id,table_id) WHERE state='active';
-- Transactional Seat command must use BEGIN IMMEDIATE, validate active/capacity
-- under the transaction, then INSERT and COMMIT; rollback on any failure.
-- Enforce venue authorization in the application before invoking the command.
-- Prevent capacity reduction below current occupancy in the application transaction.
-- This is a reference schema, not a production migration or auth layer.
