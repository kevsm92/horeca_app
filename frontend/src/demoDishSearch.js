/** Search only the synthetic POS menu. Never used for Python API authorization or pricing. */
function normalizeSearchText(value) {
  return String(value).normalize('NFD').replace(/\p{M}/gu, '').replace(/[\p{P}\p{S}]+/gu, ' ').replace(/\s+/gu, ' ').trim().toLocaleLowerCase();
}

export function filterDemoDishes(dishes, category = 'All', query = '') {
  const terms = normalizeSearchText(query).split(' ').filter(Boolean);
  return dishes.map((dish, index) => ({dish, index})).filter(({dish}) =>
    (category === 'All' || dish[2] === category) &&
    terms.every(term => normalizeSearchText(dish[0]).includes(term))
  );
}
