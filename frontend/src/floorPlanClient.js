import {parseFloorPlanResponse} from './floorPlanContract.js';

/** Same-origin, read-only transport. Server must derive venue from authenticated session. */
export async function loadFloorPlan({fetchImpl=globalThis.fetch,signal}={}) {
  if(typeof fetchImpl!=='function') throw new TypeError('Fetch unavailable');
  const response=await fetchImpl('/api/v1/floor-plan',{
    method:'GET',credentials:'same-origin',redirect:'error',headers:{Accept:'application/json'},signal
  });
  if(!response || typeof response.status!=='number')throw new Error('Invalid floor-plan response');
  if(response.status===401||response.status===403){const error=new Error('Sign in with authorized venue access to view tables.');error.code='AUTH';throw error;}
  if(!response.ok){const error=new Error('Floor plan is unavailable.');error.code='UNAVAILABLE';throw error;}
  const contentType=response.headers?.get?.('content-type')||'';
  if(!/^application\/json(?:\s*;|\s*$)/i.test(contentType))throw new Error('Floor-plan response is not JSON');
  return parseFloorPlanResponse(await response.json());
}
