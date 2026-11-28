// Historical reporting is intentionally unavailable until authenticated Python API data exists.
// Range selection changes labels only: it must never synthesize historical observations.
export const HISTORICAL_RANGES=Object.freeze([
  Object.freeze({id:'day',label:'Day'}),
  Object.freeze({id:'week',label:'Week'}),
  Object.freeze({id:'month',label:'Month'})
]);
export function historicalRangeLabel(range){
  return HISTORICAL_RANGES.find(item=>item.id===range)?.label ?? 'Week';
}
export function historicalEmptyMessage(range){
  return `No verified ${historicalRangeLabel(range).toLowerCase()} historical data is available. This is not a zero value or a live chart.`;
}
