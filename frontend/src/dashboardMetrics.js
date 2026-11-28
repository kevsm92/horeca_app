// Presentation-only synthetic metrics. Python remains authoritative for live metrics.
// Reject malformed demo fixtures rather than rendering misleading operational KPIs.
function validDemoInputs({tables,orders,orderValueCents}={}) {
  if (!Array.isArray(tables) || !Array.isArray(orders) ||
      !Number.isSafeInteger(orderValueCents) || orderValueCents < 0) {
    throw new TypeError('Invalid fictional dashboard inputs');
  }
  let totalGuests = 0;
  for (const table of tables) {
    if (!table || !Number.isSafeInteger(table.guests) || table.guests < 0) {
      throw new TypeError('Invalid fictional table occupancy');
    }
    totalGuests += table.guests;
    if (!Number.isSafeInteger(totalGuests)) {
      throw new TypeError('Fictional guest total exceeds safe integer range');
    }
  }
  for (const order of orders) {
    if (!order || typeof order.status !== 'string' || !order.status.trim()) {
      throw new TypeError('Invalid fictional order status');
    }
  }
}

export function demoDashboardMetrics({tables, orders, orderValueCents}={}) {
  validDemoInputs({tables,orders,orderValueCents});
  return [
    {id:'occupied',label:'Occupied tables',value:`${tables.filter(t=>t.guests>0).length} / ${tables.length}`,detail:'Fictional seating state',source:'demo'},
    {id:'guests',label:'Seated guests',value:String(tables.reduce((sum,t)=>sum+t.guests,0)),detail:'Fictional guest count',source:'demo'},
    {id:'tickets',label:'Kitchen tickets',value:String(orders.filter(o=>o.status!=='Ready').length),detail:'Fictional tickets not ready',source:'demo'},
    {id:'orders',label:'Demo order value',value:new Intl.NumberFormat('en-BE',{style:'currency',currency:'EUR'}).format(orderValueCents/100),detail:'Order value, not captured revenue',source:'demo'},
    {id:'presence',label:'Actually clocked in',value:null,detail:'No verified attendance API connected',source:'unavailable'},
    {id:'upcoming',label:'Upcoming shifts',value:null,detail:'No authenticated roster API connected',source:'unavailable'},
    {id:'revenue',label:'Captured revenue',value:null,detail:'No verified payment capture data',source:'unavailable'},
    {id:'requests',label:'Pending staff requests',value:null,detail:'No verified requests API connected',source:'unavailable'},
  ];
}
export function displayMetric(metric) {
  if (!metric || !['demo','unavailable'].includes(metric.source)) throw new TypeError('Unknown metric source');
  if (metric.source==='unavailable') return {...metric,value:'Unavailable',status:'Not connected'};
  if (metric.value===null || metric.value===undefined) throw new TypeError('Demo metric missing value');
  return {...metric,status:'Demo · not live'};
}
