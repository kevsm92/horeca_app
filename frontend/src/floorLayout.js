/** Synthetic visual positions only. Physical inventory and seating remain Python-owned. */
export const initialFloorPositions=Object.fromEntries(Array.from({length:8},(_,i)=>['T'+(i+1),{x:20+(i%3)*29,y:20+Math.floor(i/3)*29}]));
const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
export function moveTable(positions,id,x,y){
  if(!Object.prototype.hasOwnProperty.call(positions,id))return positions;
  if(!Number.isFinite(x)||!Number.isFinite(y))return positions;
  const point={x:clamp(x,10,90),y:clamp(y,10,90)};
  if(positions[id].x===point.x&&positions[id].y===point.y)return positions;
  return {...positions,[id]:point};
}
