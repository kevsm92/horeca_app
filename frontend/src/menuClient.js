/** Authenticated same-origin menu reads; never infer venue from browser inputs. */
const isRecord=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
export function parseMenuResponse(payload){
  if(!isRecord(payload)||!Array.isArray(payload.items)||payload.items.length>5000)throw new TypeError('Invalid menu response');
  const ids=new Set();
  return payload.items.map(item=>{
    if(!isRecord(item)||typeof item.item_id!=='string'||!/^[A-Za-z0-9_-]{1,128}$/.test(item.item_id)||ids.has(item.item_id)||
       !['food','drink'].includes(item.kind)||typeof item.name!=='string'||!item.name.trim()||item.name.length>200||
       !Number.isSafeInteger(item.price_cents)||item.price_cents<0||item.price_cents>10000000||
       typeof item.available!=='boolean'||(item.description!==null&&item.description!==undefined&&(typeof item.description!=='string'||item.description.length>2000)))
      throw new TypeError('Invalid menu item');
    ids.add(item.item_id);
    return {id:item.item_id,kind:item.kind,name:item.name,priceCents:item.price_cents,available:item.available,description:item.description??null};
  });
}
export async function loadMenu({fetchImpl=globalThis.fetch,signal,kind}={}){
  if(typeof fetchImpl!=='function')throw new TypeError('Fetch unavailable');
  if(kind!==undefined&&!['food','drink'].includes(kind))throw new TypeError('Invalid menu filter');
  if(signal?.aborted)throw new DOMException('The request was aborted.', 'AbortError');
  const url='/api/v1/menu-items'+(kind?'?kind='+kind:'');
  let response;
  try {
    response=await fetchImpl(url,{method:'GET',credentials:'same-origin',cache:'no-store',redirect:'error',headers:{Accept:'application/json'},signal});
  } catch (error) {
    // A cancelled request must not surface an obsolete transport failure as a current-view error.
    if(signal?.aborted)throw new DOMException('The request was aborted.', 'AbortError');
    throw error;
  }
  if(signal?.aborted)throw new DOMException('The request was aborted.', 'AbortError');
  if(!response||typeof response.status!=='number')throw new Error('Invalid menu HTTP response');
  if(response.status===401||response.status===403){const error=new Error('Menu authorization required');error.code='AUTH';throw error;}
  if(!response.ok){const error=new Error('Menu unavailable');error.code='UNAVAILABLE';throw error;}
  if(!/^application\/json(?:\s*;|\s*$)/i.test(response.headers?.get?.('content-type')||''))throw new TypeError('Menu response is not JSON');
  let payload;
  try { payload=await response.json(); }
  catch (error) {
    // Cancellation wins over a late JSON parsing/network error from an obsolete view.
    if(signal?.aborted)throw new DOMException('The request was aborted.', 'AbortError');
    throw error;
  }
  // A cancelled request must never publish a late response from a previous view/session.
  if(signal?.aborted)throw new DOMException('The request was aborted.', 'AbortError');
  return parseMenuResponse(payload);
}
