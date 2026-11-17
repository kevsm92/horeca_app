/** Strict adapter for a future authenticated Python floor-plan read response.
 * This module never treats browser-supplied venue identifiers as authorization.
 */
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const record=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const coordinate=v=>typeof v==='number'&&Number.isFinite(v)&&v>=10&&v<=90;
export function parseFloorPlanResponse(payload){
  if(!record(payload)||!Number.isSafeInteger(payload.revision)||payload.revision<0||!Array.isArray(payload.tables)||!Array.isArray(payload.placements))throw new TypeError('Invalid floor-plan response');
  const inventory=new Map();
  for(const t of payload.tables){
    if(!record(t)||typeof t.id!=='string'||!/^[-A-Za-z0-9_]{1,64}$/.test(t.id)||inventory.has(t.id)||!Number.isSafeInteger(t.physical_seats)||t.physical_seats<1||t.physical_seats>100||!Number.isSafeInteger(t.occupied_guests)||t.occupied_guests<0||t.occupied_guests>t.physical_seats)throw new TypeError('Invalid physical table inventory');
    inventory.set(t.id,{id:t.id,seats:t.physical_seats,guests:t.occupied_guests});
  }
  const positions=Object.create(null);
  for(const p of payload.placements){
    if(!record(p)||typeof p.table_id!=='string'||!inventory.has(p.table_id)||own(positions,p.table_id)||!coordinate(p.x_percent)||!coordinate(p.y_percent))throw new TypeError('Invalid floor-plan placement');
    positions[p.table_id]={x:p.x_percent,y:p.y_percent};
  }
  return {revision:payload.revision,tables:[...inventory.values()],positions};
}
export function floorPlanPatch(expectedRevision,positions){
  if(!Number.isSafeInteger(expectedRevision)||expectedRevision<0||!record(positions))throw new TypeError('Invalid floor-plan edit');
  const operations=[];
  for(const [table_id,p] of Object.entries(positions)){
    if(!/^[-A-Za-z0-9_]{1,64}$/.test(table_id)||!record(p)||!coordinate(p.x)||!coordinate(p.y))throw new TypeError('Invalid floor-plan edit');
    operations.push({type:'move',table_id,x_percent:p.x,y_percent:p.y});
  }
  return {expected_revision:expectedRevision,operations};
}
