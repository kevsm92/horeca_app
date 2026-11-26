/** Presentation-only shift details. No inferred attendance or persistence. */
export function rosterShiftKey(personId, date) {
  if (!/^[a-z0-9_-]{1,64}$/i.test(personId) || !/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new TypeError('Invalid shift identity');
  return `${personId}:${date}`;
}
export function rosterShiftDescription(person, day, shift) {
  if (!person || !day || !shift || typeof shift.time !== 'string') throw new TypeError('Missing planned shift');
  return `${person.name} (${person.role}), ${day.day} ${day.date}: ${shift.time}. Scheduled only; actual attendance unknown. Fictional data; no changes saved.`;
}
