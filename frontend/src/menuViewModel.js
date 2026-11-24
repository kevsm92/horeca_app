/** Read-only view model for authenticated Python menu catalog. */
const searchKey = value => value.normalize('NFD').replace(/\p{M}/gu, '').replace(/['’]/gu, '').replace(/[\p{P}\p{S}]/gu, ' ').replace(/\s+/gu, ' ').trim().toLocaleLowerCase();
export function filterMenu(items,query='',kind='all',availableOnly=false){
  if(!Array.isArray(items)||typeof query!=='string'||!['all','food','drink'].includes(kind)||typeof availableOnly!=='boolean')throw new TypeError('Invalid menu filter');
  const terms=searchKey(query).split(' ').filter(Boolean);
  return items.filter(item=>{
    if(kind!=='all'&&item.kind!==kind)return false;
    if(availableOnly&&!item.available)return false;
    if(terms.length===0)return true;
    const searchable=searchKey([item.name,item.description??''].join(' '));
    return terms.every(term=>searchable.includes(term));
  });
}

/** Presentation-only ordering; never changes authoritative Python menu records. */
export function sortMenu(items,order='default'){
  if(!Array.isArray(items)||!['default','name','price-low','price-high'].includes(order))throw new TypeError('Invalid menu sort');
  if(order==='default')return [...items];
  const collator=new Intl.Collator('en-BE',{sensitivity:'base',numeric:true});
  return items.map((item,index)=>({item,index})).sort((a,b)=>{
    const comparison=order==='name'?collator.compare(a.item.name,b.item.name):
      order==='price-low'?a.item.priceCents-b.item.priceCents:b.item.priceCents-a.item.priceCents;
    return comparison||a.index-b.index;
  }).map(entry=>entry.item);
}
