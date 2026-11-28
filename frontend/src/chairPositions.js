/** Decorative seat positions only. Never used to authorize seating or alter capacity. */
export function chairPositions(capacity) {
  if (!Number.isInteger(capacity) || capacity < 1 || capacity > 30) return [];
  const sides = ['top', 'right', 'bottom', 'left'];
  return Array.from({ length: capacity }, (_, index) => {
    const side = sides[index % 4];
    const slot = Math.floor(index / 4);
    const count = Math.ceil((capacity - (index % 4)) / 4);
    return Object.freeze({ side, offset: (slot + 1) * 100 / (count + 1) });
  });
}
