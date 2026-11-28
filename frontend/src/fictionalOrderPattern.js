// Static, synthetic illustration only. Never substitute for authenticated venue metrics.
export const FICTIONAL_WEEKLY_ORDERS = Object.freeze([
  Object.freeze({day:'Mon',count:8}),
  Object.freeze({day:'Tue',count:12}),
  Object.freeze({day:'Wed',count:10}),
  Object.freeze({day:'Thu',count:16}),
  Object.freeze({day:'Fri',count:24}),
  Object.freeze({day:'Sat',count:28}),
  Object.freeze({day:'Sun',count:18}),
]);
export function fictionalOrderBarPercent(count) {
  if (!Number.isFinite(count) || count < 0) return 0;
  const max = Math.max(...FICTIONAL_WEEKLY_ORDERS.map(item => item.count));
  return Math.min(100, count / max * 100);
}
