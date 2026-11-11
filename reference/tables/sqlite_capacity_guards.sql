-- Apply after sqlite_seating_schema.sql; SQLite offline reference only.
-- Protect active sessions even when callers bypass the intended Seat command.
CREATE TRIGGER IF NOT EXISTS seating_insert_guard
BEFORE INSERT ON seating_sessions
WHEN NEW.state='active'
BEGIN
 SELECT RAISE(ABORT, 'table inactive or capacity exceeded')
 WHERE NOT EXISTS (
  SELECT 1 FROM physical_tables t
  WHERE t.venue_id=NEW.venue_id AND t.table_id=NEW.table_id
    AND t.active=1 AND NEW.guest_count<=t.capacity_seats
 );
END;

CREATE TRIGGER IF NOT EXISTS seating_update_guard
BEFORE UPDATE OF venue_id,table_id,guest_count,state ON seating_sessions
WHEN NEW.state='active'
BEGIN
 SELECT RAISE(ABORT, 'table inactive or capacity exceeded')
 WHERE NOT EXISTS (
  SELECT 1 FROM physical_tables t
  WHERE t.venue_id=NEW.venue_id AND t.table_id=NEW.table_id
    AND t.active=1 AND NEW.guest_count<=t.capacity_seats
 );
END;

CREATE TRIGGER IF NOT EXISTS table_capacity_guard
BEFORE UPDATE OF capacity_seats,active ON physical_tables
BEGIN
 SELECT RAISE(ABORT, 'active seating exceeds new table capacity or table deactivated')
 WHERE EXISTS (
  SELECT 1 FROM seating_sessions s
  WHERE s.venue_id=NEW.venue_id AND s.table_id=NEW.table_id
    AND s.state='active' AND (NEW.active=0 OR s.guest_count>NEW.capacity_seats)
 );
END;
