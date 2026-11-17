/** Synthetic reservations for the frontend demo only; not an availability engine. */
export const demoReservations = Object.freeze([
  Object.freeze({ id: 'demo-r1', time: '19:00', name: 'Alex Morgan', guests: 2, table: 'T1' }),
  Object.freeze({ id: 'demo-r2', time: '20:00', name: 'Jamie Lee', guests: 4, table: 'T3' })
]);

export function filterDemoReservations(reservations, query = '') {
  const term = String(query).trim().toLocaleLowerCase();
  if (!term) return [...reservations];
  return reservations.filter(reservation =>
    [reservation.name, reservation.table, reservation.time]
      .some(value => String(value).toLocaleLowerCase().includes(term))
  );
}
