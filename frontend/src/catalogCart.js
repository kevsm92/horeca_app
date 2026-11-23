/** Offline POS cart projection for authenticated Python menu records.
 * Never trusts client-side totals for a future checkout API.
 */
const MAX_QUANTITY = 99;
const MAX_TOTAL_CENTS = 1000000000;

export function catalogCartLines(items, quantities) {
  if (!Array.isArray(items) || quantities === null || typeof quantities !== 'object' || Array.isArray(quantities))
    throw new TypeError('Invalid catalog cart');
  const byId = new Map();
  for (const item of items) {
    if (!item || typeof item.id !== 'string' || !/^[A-Za-z0-9_-]{1,128}$/.test(item.id) || byId.has(item.id) ||
        typeof item.name !== 'string' || !item.name.trim() ||
        !Number.isSafeInteger(item.priceCents) || item.priceCents < 0 || item.priceCents > 10000000 ||
        typeof item.available !== 'boolean') throw new TypeError('Invalid catalog item');
    byId.set(item.id, item);
  }
  const lines = [];
  let totalCents = 0;
  for (const [id,quantity] of Object.entries(quantities)) {
    if (!Number.isSafeInteger(quantity) || quantity < 1 || quantity > MAX_QUANTITY)
      throw new RangeError('Invalid cart quantity');
    const item = byId.get(id);
    if (!item || !item.available) throw new RangeError('Unknown or unavailable catalog item');
    const lineCents = item.priceCents * quantity;
    if (!Number.isSafeInteger(lineCents) || totalCents + lineCents > MAX_TOTAL_CENTS)
      throw new RangeError('Cart total limit exceeded');
    totalCents += lineCents;
    lines.push({id, name:item.name, quantity, unitPriceCents:item.priceCents, lineCents});
  }
  return {lines, totalCents};
}

export function changeCatalogQuantity(items, quantities, id, delta) {
  if (typeof id !== 'string' || !Number.isSafeInteger(delta) || ![-1,1].includes(delta))
    throw new TypeError('Invalid cart adjustment');
  const current = quantities != null && Object.hasOwn(quantities, id) ? quantities[id] : 0;
  if (!Number.isSafeInteger(current) || current < 0 || current > MAX_QUANTITY)
    throw new RangeError('Invalid current quantity');
  const next = current + delta;
  if (next < 0 || next > MAX_QUANTITY) throw new RangeError('Cart quantity limit exceeded');
  const updated = {...quantities};
  if (next === 0) delete updated[id];
  else Object.defineProperty(updated, id, {value:next, enumerable:true, writable:true, configurable:true});
  catalogCartLines(items, updated);
  return updated;
}

/** Remove one entire local draft line; no order mutation or server write. */
export function removeCatalogLine(items, quantities, id) {
  if (typeof id !== 'string' || !Object.hasOwn(quantities ?? {}, id))
    throw new RangeError('Unknown cart line');
  catalogCartLines(items, quantities);
  const updated = {...quantities};
  delete updated[id];
  catalogCartLines(items, updated);
  return updated;
}
