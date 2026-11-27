// Frontend presentation states only. No network requests or claims of an available Python route.
// The Python API must supply authenticated, venue-scoped records before a real 'ready' state is used.
export const HISTORICAL_VIEW_STATES = Object.freeze(['unavailable','loading','empty','error','stale','forbidden']);

export function historicalViewMessage(state='unavailable') {
  const messages = {
    unavailable: {title:'Data unavailable', detail:'Historical records are not connected to an authenticated Python API.', retry:false},
    loading: {title:'Loading historical records', detail:'Waiting for the authorized Python API response.', retry:false},
    empty: {title:'No records for this period', detail:'The authorized source returned no records for the selected period.', retry:false},
    error: {title:'Historical records could not be loaded', detail:'The request failed. No historical totals are displayed.', retry:true},
    stale: {title:'Historical records may be outdated', detail:'Freshness could not be confirmed. Do not treat cached values as current.', retry:true},
    forbidden: {title:'Access not permitted', detail:'The current session is not authorized to view these records.', retry:false},
  };
  if (!Object.hasOwn(messages,state)) throw new TypeError('Unknown historical view state');
  return Object.freeze({...messages[state],state});
}
