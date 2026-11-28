// Pure, synthetic-data table-session rules. No browser storage or network calls.
export function validateGuestCount(table, nextGuests) {
  if (!table || !Number.isInteger(table.seats) || table.seats < 1) return { ok: false, reason: 'Invalid physical table capacity.' };
  if (!Number.isInteger(nextGuests) || nextGuests < 0) return { ok: false, reason: 'Guest count must be a non-negative integer.' };
  if (nextGuests > table.seats) return { ok: false, reason: 'Physical table capacity cannot be exceeded.' };
  return { ok: true };
}

export function updateGuestCount(tables, tableId, delta) {
  const table = tables.find(t => t.id === tableId);
  if (!table) return { ok: false, reason: 'Table not found.', tables };
  if (!Number.isInteger(delta)) return { ok: false, reason: 'Guest count change must be an integer.', tables };
  const nextGuests = table.guests + delta;
  const validation = validateGuestCount(table, nextGuests);
  if (!validation.ok) return { ...validation, tables };
  return { ok: true, tables: tables.map(t => t.id === tableId ? { ...t, guests: nextGuests } : t) };
}

export function canSubmitOrder(table, cartTotal) {
  if (!Number.isSafeInteger(cartTotal) || cartTotal <= 0) return { ok: false, reason: 'Add menu items first.' };
  if (!table || !Number.isInteger(table.guests) || table.guests < 1) return { ok: false, reason: 'Seat guests before sending an order.' };
  return validateGuestCount(table, table.guests);
}
