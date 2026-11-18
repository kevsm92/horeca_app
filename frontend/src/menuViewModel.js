/** Read-only view model for authenticated Python menu catalog. */
export function filterMenu(items,query='',kind='all'){
  if(!Array.isArray(items)||typeof query!=='string'||!['all','food','drink'].includes(kind))throw new TypeError('Invalid menu filter');
  const term=query.trim().toLocaleLowerCase();
  return items.filter(item=>(kind==='all'||item.kind===kind)&&item.name.toLocaleLowerCase().includes(term));
}
