/** Search only the synthetic POS menu. Never used for Python API authorization or pricing. */
function normalizeSearchText(value) {
  return String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
}

export function filterDemoDishes(dishes, category = 'All', query = '') {
  const term = normalizeSearchText(query).trim();
  return dishes.map((dish, index) => ({dish, index})).filter(({dish}) =>
    (category === 'All' || dish[2] === category) &&
    normalizeSearchText(dish[0]).includes(term)
  );
}
