/** Browser-only floor-plan pointer geometry; never changes physical seating or Python data. */
export function pointerFloorPosition(origin, start, current, bounds) {
  if (!origin || !start || !current || !bounds) return null;
  const values = [origin.x, origin.y, start.x, start.y, current.x, current.y, bounds.width, bounds.height];
  if (!values.every(Number.isFinite) || bounds.width <= 0 || bounds.height <= 0) return null;
  const x = origin.x + (current.x - start.x) / bounds.width * 100;
  const y = origin.y + (current.y - start.y) / bounds.height * 100;
  return Number.isFinite(x) && Number.isFinite(y) ? { x, y } : null;
}
