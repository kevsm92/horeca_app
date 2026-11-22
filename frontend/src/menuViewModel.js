/** Read-only view model for authenticated Python menu catalog. */
const searchKey = value => value.normalize('NFD').replace(/\p{M}/gu, '').replace(/['’]/gu, '').replace(/[\p{Pd}/]/gu, ' ').replace(/\s+/gu, ' ').trim().toLocaleLowerCase();
export function filterMenu(items,query='',kind='all'){
  if(!Array.isArray(items)||typeof query!=='string'||!['all','food','drink'].includes(kind))throw new TypeError('Invalid menu filter');
  const terms=searchKey(query).split(' ').filter(Boolean);
  return items.filter(item=>{
    if(kind!=='all'&&item.kind!==kind)return false;
    if(terms.length===0)return true;
    const searchable=searchKey([item.name,item.description??''].join(' '));
    return terms.every(term=>searchable.includes(term));
  });
}
