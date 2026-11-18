/** Search only the synthetic POS menu. Never used for Python API authorization or pricing. */
export function filterDemoDishes(dishes, category = 'All', query = '') {
  const term = String(query).trim().toLocaleLowerCase();
  return dishes.map((dish, index) => ({dish, index})).filter(({dish}) =>
    (category === 'All' || dish[2] === category) &&
    dish[0].toLocaleLowerCase().includes(term)
  );
}
