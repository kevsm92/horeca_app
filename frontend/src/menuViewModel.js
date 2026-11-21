/** Read-only view model for authenticated Python menu catalog. */
const searchKey = value => value.normalize('NFD').replace(/\p{M}/gu, '').replace(/\s+/gu, ' ').trim().toLocaleLowerCase();
export function filterMenu(items,query='',kind='all'){
  if(!Array.isArray(items)||typeof query!=='string'||!['all','food','drink'].includes(kind))throw new TypeError('Invalid menu filter');
  const terms=searchKey(query).split(' ').filter(Boolean);
  return items.filter(item=>(kind==='all'||item.kind===kind)&&terms.every(term=>searchKey(item.name).includes(term)));
}
