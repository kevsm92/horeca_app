/** Synthetic reservations for the frontend demo only; not an availability engine. */
export const demoReservations = Object.freeze([
  Object.freeze({ id: 'demo-r1', time: '19:00', name: 'Alex Morgan', guests: 2, table: 'T1' }),
  Object.freeze({ id: 'demo-r2', time: '20:00', name: 'Jamie Lee', guests: 4, table: 'T3' })
]);

// Normalize accents for forgiving local demo search only; never for authorization or availability.
const searchKey = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();

export function filterDemoReservations(reservations, query = '') {
  const term = searchKey(query).trim();
  if (!term) return [...reservations];
  return reservations.filter(reservation =>
    [reservation.name, reservation.table, reservation.time]
      .some(value => searchKey(value).includes(term))
  );
}
