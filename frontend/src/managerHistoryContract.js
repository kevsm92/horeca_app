/** Frontend-only PROPOSED v1 historical metrics contract. Not an active route.
 * Python must verify endpoint, session/venue scoping and authorization before use.
 */
export const HISTORY_METRICS = Object.freeze(['orders', 'captured_revenue', 'occupied_tables', 'actual_attendance']);
export class HistoryContractError extends Error {
  constructor(message) { super(message); this.name = 'HistoryContractError'; }
}
const fail = () => { throw new HistoryContractError('Invalid manager history response.'); };
const isRecord = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const isoInstant = value => typeof value === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(value) && Number.isFinite(Date.parse(value));
const isoDay = value => typeof value === 'string' && /^\d{4}-\d\d-\d\d$/.test(value) && !Number.isNaN(Date.parse(value + 'T00:00:00Z')) && new Date(value + 'T00:00:00Z').toISOString().slice(0,10) === value;
/** Rejects malformed, cross-venue-unverifiable and fabricated/ambiguous values.
 * Venue identity is NEVER accepted from user-controlled request parameters.
 * The expected venue comes from a trusted authenticated application context.
 */
export function parseManagerHistory(payload, {expectedVenueId, range} = {}) {
  if (!isRecord(payload) || payload.schema_version !== 1 ||
      typeof expectedVenueId !== 'string' || !expectedVenueId.trim() ||
      payload.venue_id !== expectedVenueId || !['day','week','month'].includes(range) ||
      payload.range !== range || !isoInstant(payload.generated_at) ||
      typeof payload.timezone !== 'string' || !/^[A-Za-z_]+\/[A-Za-z_]+(?:\/[A-Za-z_]+)?$/.test(payload.timezone) ||
      !isoDay(payload.period_start) || !isoDay(payload.period_end) || payload.period_end < payload.period_start ||
      !Array.isArray(payload.series) || payload.series.length !== HISTORY_METRICS.length) fail();
  const expectedUnits = {orders:'count',captured_revenue:'minor_currency',occupied_tables:'count',actual_attendance:'count'};
  const seen = new Set();
  const series = payload.series.map(item => {
    if (!isRecord(item) || !HISTORY_METRICS.includes(item.metric) || seen.has(item.metric) ||
        item.unit !== expectedUnits[item.metric] || !Array.isArray(item.points)) fail();
    seen.add(item.metric);
    let previous = -Infinity;
    const points = item.points.map(point => {
      if (!isRecord(point) || !isoInstant(point.at) || Date.parse(point.at) <= previous ||
          !Number.isSafeInteger(point.value) || point.value < 0) fail();
      previous = Date.parse(point.at);
      return Object.freeze({at:point.at,value:point.value});
    });
    return Object.freeze({metric:item.metric,unit:item.unit,points:Object.freeze(points)});
  });
  if (seen.size !== HISTORY_METRICS.length) fail();
  if (typeof payload.currency !== 'string' || !/^[A-Z]{3}$/.test(payload.currency)) fail();
  return Object.freeze({schemaVersion:1,venueId:payload.venue_id,range:payload.range,
    generatedAt:payload.generated_at,timezone:payload.timezone,currency:payload.currency,
    periodStart:payload.period_start,periodEnd:payload.period_end,series:Object.freeze(series)});
}
