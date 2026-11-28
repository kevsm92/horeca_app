/** Synthetic visual positions only. Physical inventory and seating remain Python-owned. */
export const initialFloorPositions=Object.fromEntries(Array.from({length:8},(_,i)=>['T'+(i+1),{x:20+(i%3)*29,y:20+Math.floor(i/3)*29}]));
const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
// Keep draggable demo table centers separated to avoid overlapping controls.
// This is a visual-only guard, NOT a seating/capacity or venue authorization rule.
const MIN_CENTER_GAP=12;
export function moveTable(positions,id,x,y){
  if(!positions || typeof positions!=='object' || !Object.prototype.hasOwnProperty.call(positions,id))return positions;
  const current=positions[id];
  if(!current || !Number.isFinite(current.x) || !Number.isFinite(current.y))return positions;
  if(!Number.isFinite(x)||!Number.isFinite(y))return positions;
  const point={x:clamp(x,10,90),y:clamp(y,10,90)};
  if(current.x===point.x&&current.y===point.y)return positions;
  if(Object.entries(positions).some(([otherId,other])=>otherId!==id&&other&&Number.isFinite(other.x)&&Number.isFinite(other.y)&&Math.abs(other.x-point.x)<MIN_CENTER_GAP&&Math.abs(other.y-point.y)<MIN_CENTER_GAP))return positions;
  return {...positions,[id]:point};
}
