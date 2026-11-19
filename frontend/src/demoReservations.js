/** Synthetic reservations for the frontend demo only; not an availability engine. */
export const demoReservations = Object.freeze([
  Object.freeze({ id: 'demo-r1', time: '19:00', name: 'Alex Morgan', guests: 2, table: 'T1' }),
  Object.freeze({ id: 'demo-r2', time: '20:00', name: 'Jamie Lee', guests: 4, table: 'T3' })
]);

// Forgiving local demo search only; never use for authorization or availability.
const searchKey = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase().replace(/\s+/gu, ' ').trim();

export function filterDemoReservations(reservations, query = '') {
  const terms = searchKey(query).split(' ').filter(Boolean);
  if (!terms.length) return [...reservations];
  return reservations.filter(reservation => {
    const fields = [reservation.name, reservation.table, reservation.time].map(searchKey);
    return terms.every(term => fields.some(field => field.includes(term)));
  });
}
