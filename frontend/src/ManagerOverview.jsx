import React,{useState} from 'react';
import {historicalRangeLabel,historicalEmptyMessage,HISTORICAL_RANGES} from './historicalMetrics.js';
import {demoDashboardMetrics,displayMetric} from './dashboardMetrics.js';
import './managerOverview.css';
export default function ManagerOverview({tables,orders,orderValueCents,onTables,onOrders,onStaff}) {
  const [range,setRange]=useState('week');
  const metrics=demoDashboardMetrics({tables,orders,orderValueCents}).map(displayMetric);
  return <section aria-labelledby="manager-overview-title" className="manager-overview">
    <div className="manager-overview-heading"><div><h2 id="manager-overview-title">Manager overview</h2><p>Fictional venue preview. Live workforce and financial totals are not connected.</p></div><span className="manager-overview-mode">DEMO · NOT LIVE</span></div>
    <div className="manager-overview-metrics">{metrics.map(metric=><article key={metric.id} className="manager-overview-metric"><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.status}</small><p>{metric.detail}</p></article>)}</div>
    <div className="manager-overview-actions"><button type="button" onClick={onTables}>Open floor plan</button><button type="button" onClick={onOrders}>Take order</button><button type="button" onClick={onStaff}>Open weekly staff roster</button></div>
    <section className="manager-history" aria-labelledby="manager-history-title">
      <div className="manager-history-heading"><div><h3 id="manager-history-title">Operational trends</h3><p>Historical records are not connected to an authenticated Python API.</p></div>
        <label htmlFor="manager-history-range">Time range <select id="manager-history-range" value={range} onChange={event=>setRange(event.target.value)}>{HISTORICAL_RANGES.map(item=><option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
      </div>
      <div className="manager-history-empty" role="status" aria-live="polite"><strong>Data unavailable</strong><p>{historicalEmptyMessage(range)}</p></div>
      <table className="manager-history-table"><caption>Historical operational metrics · {historicalRangeLabel(range)} · unavailable</caption><thead><tr><th scope="col">Metric</th><th scope="col">Selected period</th><th scope="col">Status</th></tr></thead><tbody>{['Orders','Captured revenue','Occupied tables','Actual staff attendance'].map(name=><tr key={name}><th scope="row">{name}</th><td>{historicalRangeLabel(range)}</td><td>Unavailable</td></tr>)}</tbody></table>
    </section>
    <p className="manager-overview-note">Scheduled shifts never establish actual presence. Demo order value does not represent captured revenue. No historical chart is shown without verified historical records.</p>
  </section>;
}
